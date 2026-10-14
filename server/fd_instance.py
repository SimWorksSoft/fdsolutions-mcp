import concurrent.futures
import json
import logging
import os
import sys
import threading
from typing import Any, Callable, Optional, Tuple

_fd_real_instance = None
_fd_initialized = False
_fd_attach = False
_fd_server_name = None

# mcp 2.x runs sync tool handlers on worker threads. simworks / script_channel
# is not thread-safe, so all FD create + API calls must stay on one dedicated thread.
_fd_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="fd-api"
)
_fd_thread_id: Optional[int] = None
_fd_thread_ready = threading.Event()

logger = logging.getLogger(__name__)


def _ensure_fd_thread() -> None:
    global _fd_thread_id
    if _fd_thread_ready.is_set():
        return

    def _mark() -> None:
        global _fd_thread_id
        _fd_thread_id = threading.get_ident()
        _fd_thread_ready.set()

    _fd_executor.submit(_mark).result()


def _run_on_fd_thread(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run fn on the dedicated FD API thread (avoids mcp 2.x worker-thread races)."""
    _ensure_fd_thread()
    if threading.get_ident() == _fd_thread_id:
        return fn(*args, **kwargs)
    return _fd_executor.submit(fn, *args, **kwargs).result()


def _is_valid_python_api_dir(path: str) -> bool:
    if not path:
        return False
    abs_path = os.path.abspath(path)
    return os.path.isdir(abs_path) and os.path.isfile(os.path.join(abs_path, "simworks.py"))


def _install_root_from_python_api(python_api_path: str) -> Optional[str]:
    """Infer software install root from api/python (…/install/api/python → …/install)."""
    abs_api = os.path.abspath(python_api_path)
    parent = os.path.dirname(abs_api)
    if os.path.basename(abs_api).lower() == "python" and os.path.basename(parent).lower() == "api":
        return os.path.dirname(parent)
    return None


def _add_dll_directory_if_needed(install_root: Optional[str]) -> None:
    if not install_root or sys.platform != "win32":
        return
    bin_dir = os.path.join(install_root, "bin")
    if os.path.isdir(bin_dir) and hasattr(os, "add_dll_directory"):
        os.add_dll_directory(bin_dir)
        logger.debug("Added DLL directory: %s", bin_dir)


def _resolve_from_env() -> Optional[Tuple[str, Optional[str]]]:
    """Return (python_api_path, install_root) from environment, or None."""
    python_api = os.environ.get("FDSOLUTIONS_PYTHON_API", "").strip()
    if python_api and _is_valid_python_api_dir(python_api):
        install_root = _install_root_from_python_api(python_api)
        return os.path.abspath(python_api), install_root

    home = os.environ.get("FDSOLUTIONS_HOME", "").strip()
    if home:
        candidate = os.path.join(home, "api", "python")
        if _is_valid_python_api_dir(candidate):
            return os.path.abspath(candidate), os.path.abspath(home)

    return None


def _config_search_paths() -> list:
    paths = []
    cwd_cfg = os.path.join(os.getcwd(), "config.json")
    paths.append(cwd_cfg)

    module_dir = os.path.dirname(os.path.abspath(__file__))
    module_cfg = os.path.join(module_dir, "config.json")
    if module_cfg not in paths:
        paths.append(module_cfg)

    return paths


def _resolve_from_config() -> Optional[Tuple[str, Optional[str]]]:
    """Return (python_api_path, install_root) from config.json, or None."""
    for cfg_path in _config_search_paths():
        if not os.path.isfile(cfg_path):
            continue
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to read config %s: %s", cfg_path, e)
            continue

        if not isinstance(data, dict):
            continue

        cfg_dir = os.path.dirname(os.path.abspath(cfg_path))

        python_api_path = data.get("python_api_path")
        if python_api_path:
            if not os.path.isabs(python_api_path):
                python_api_path = os.path.normpath(os.path.join(cfg_dir, python_api_path))
            if _is_valid_python_api_dir(python_api_path):
                install_root = _install_root_from_python_api(python_api_path)
                # Prefer explicit install root from fd_solutions_path if also present
                fd_root = data.get("fd_solutions_path")
                if fd_root:
                    if not os.path.isabs(fd_root):
                        fd_root = os.path.normpath(os.path.join(cfg_dir, fd_root))
                    if os.path.isdir(fd_root):
                        install_root = os.path.abspath(fd_root)
                return os.path.abspath(python_api_path), install_root

        fd_root = data.get("fd_solutions_path")
        if fd_root:
            if not os.path.isabs(fd_root):
                fd_root = os.path.normpath(os.path.join(cfg_dir, fd_root))
            candidate = os.path.join(fd_root, "api", "python")
            if _is_valid_python_api_dir(candidate):
                return os.path.abspath(candidate), os.path.abspath(fd_root)

    return None


def _resolve_python_api() -> Tuple[str, Optional[str]]:
    """
    Resolve simworks Python API directory.

    Order: FDSOLUTIONS_* env → config.json → raise RuntimeError.
    Returns (python_api_path, install_root_or_None).
    """
    resolved = _resolve_from_env()
    if resolved:
        return resolved

    resolved = _resolve_from_config()
    if resolved:
        return resolved

    raise RuntimeError(
        "Cannot locate FD Solutions Python API. "
        "Set environment variable FDSOLUTIONS_PYTHON_API (directory containing simworks.py) "
        "or FDSOLUTIONS_HOME (install root, expects api/python), "
        "or provide a config.json with python_api_path "
        "(searched in the current working directory and next to server.py). "
        "See config.example.json."
    )


def configure_fd(attach: bool = False, server_name: str = None) -> None:
    """Store FD launch options for lazy initialization on first tool use."""
    global _fd_attach, _fd_server_name
    if _fd_initialized:
        logger.warning("configure_fd() ignored because FD is already initialized")
        return
    _fd_attach = bool(attach)
    _fd_server_name = server_name


def _initialize_fd_unlocked(attach: bool = None, server_name: str = None):
    """Create FD on the current thread. Must only run on the dedicated FD API thread."""
    global _fd_real_instance, _fd_initialized, _fd_attach, _fd_server_name
    if not _fd_initialized:
        if attach is not None:
            _fd_attach = bool(attach)
        if server_name is not None:
            _fd_server_name = server_name

        logger.info("Initializing FD Solutions (lazy)...")
        python_api_path, install_root = _resolve_python_api()
        _add_dll_directory_if_needed(install_root)
        if python_api_path not in sys.path:
            sys.path.insert(0, python_api_path)
        import simworks
        args = dict()
        if _fd_attach:
            args["attach"] = ''
            args["server_name"] = _fd_server_name
        _fd_real_instance = simworks.FD(args=args)
        _fd_initialized = True
        logger.info("FD Solutions initialized")
    return _fd_real_instance


def _initialize_fd(attach: bool = None, server_name: str = None):
    return _run_on_fd_thread(_initialize_fd_unlocked, attach, server_name)


class _FDProxy:
    """Proxy that marshals every FD attribute access/call onto the FD API thread."""

    def __getattr__(self, name: str) -> Any:
        def _resolve() -> Any:
            real_obj = _initialize_fd_unlocked()
            return getattr(real_obj, name)

        attr = _run_on_fd_thread(_resolve)
        if not callable(attr):
            return attr

        def _bound(*args: Any, **kwargs: Any) -> Any:
            def _invoke() -> Any:
                real_obj = _initialize_fd_unlocked()
                return getattr(real_obj, name)(*args, **kwargs)

            return _run_on_fd_thread(_invoke)

        return _bound

    def __setattr__(self, key: str, value: Any) -> None:
        def _set() -> None:
            real_obj = _initialize_fd_unlocked()
            setattr(real_obj, key, value)

        _run_on_fd_thread(_set)


fd_instance = _FDProxy()


def initialize_fd(attach: bool = False, server_name: str = None):
    """Eagerly create the FD instance (prefer configure_fd + lazy proxy for MCP)."""
    _initialize_fd(attach=attach, server_name=server_name)
