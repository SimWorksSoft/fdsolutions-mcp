"""Workspace clear, load, and save (enum). Low-level file I/O included."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

WorkspaceAction = Literal[
    "clear",
    "clear_all",
    "clc",
    "clear_global",
    "clear_all_global",
]

LoadKind = Literal[
    "script",
    "mdf",
    "mat",
    "h5",
    "ascii",
    "rfile",
    "nk_file",
    "nk_array",
    "readm",
    "readascii",
    "readb",
    "readgraph",
    "fread",
]

SaveKind = Literal["mdf", "mat", "h5", "ascii"]

FileIoAction = Literal["fopen", "fclose", "fwrite", "write", "writem", "writeascii", "spwrite"]


@mcp_instance.tool(title="Workspace")
def workspace_action(
    action: Annotated[WorkspaceAction, Field(description="Clear workspace / console / globals.")],
    names: Annotated[Optional[list[str]], Field(description="Variable names for clear / clear_global.")] = None,
    name: Annotated[Optional[str], Field(description="Single global name for clear_global.")] = None,
) -> str:
    """Clear workspace variables or the script console."""
    try:
        if action == "clear":
            if names:
                args = ", ".join(f'"{n}"' for n in names)
                fd_instance.eval(f"clear({args});")
                return f"Cleared variables {names}."
            fd_instance.clear()
            return "Workspace cleared."
        if action == "clear_all":
            fd_instance.clearall()
            return "All workspace cleared."
        if action == "clc":
            fd_instance.eval("clc;")
            return "Script console cleared."
        if action == "clear_global":
            var = name or (names[0] if names else None)
            if not var:
                return "ERROR: name required for clear_global."
            fd_instance.eval(f'clearglobalvariable("{var}");')
            return f"Cleared global '{var}'."
        if action == "clear_all_global":
            fd_instance.clearallglobalvariable()
            return "All globals cleared."
        return f"ERROR: Unknown action {action!r}"
    except Exception as e:
        return f"ERROR: workspace_action({action}) failed: {e}"


@mcp_instance.tool(title="Load data")
def load_data(
    kind: Annotated[
        LoadKind,
        Field(
            description=(
                "script: load() a .msf (or other) script file and run it. "
                "Other kinds load data / NK / raw reads into the workspace."
            ),
        ),
    ],
    file_path: Annotated[
        Optional[str],
        Field(description="File path. Prefer absolute paths (required for most kinds)."),
    ] = None,
    var: Annotated[Optional[str], Field(description="Optional workspace variable target.")] = None,
    file_units: Annotated[str, Field(description="NK file units.")] = "m",
    x0: float = 0.0,
    y0: float = 0.0,
    z0: float = 0.0,
    reverse_index: int = 0,
    n_array: Annotated[Optional[list], Field(description="NK array for nk_array.")] = None,
    x_vec: Annotated[Optional[list], Field(description="X vector for nk_array.")] = None,
    y_vec: Annotated[Optional[list], Field(description="Y vector for nk_array.")] = None,
    z_vec: Annotated[Optional[list], Field(description="Z vector for nk_array.")] = None,
    nitems: Annotated[Optional[int], Field(description="fread item count.")] = None,
    type_name: Annotated[Optional[str], Field(description="fread type.")] = None,
    swapb: int = 0,
    size: Annotated[Optional[Any], Field(description="Optional readm size.")] = None,
    x: Annotated[Optional[Any], Field(description="Optional readascii x.")] = None,
) -> str:
    """Load a script file, data files, or import NK / raw arrays into the workspace.

    - kind="script": SimWorks load('file_path') — loads and runs a script
      (e.g. .msf). Prefer an absolute path.
    - To open a project (.sim / .mpps etc.), use project_action(action="open").
    - Other kinds load data into the workspace (mdf/mat/h5/…), not scripts.
    """
    try:
        if kind == "script":
            if not file_path:
                return "ERROR: file_path required for script (load)."
            fd_instance.load(file_path)
            return f"Loaded and ran script '{file_path}'."

        if kind == "nk_array":
            if n_array is None or x_vec is None or y_vec is None or z_vec is None:
                return "ERROR: n_array, x_vec, y_vec, z_vec required for nk_array."
            fd_instance.importnk2(n_array, x_vec, y_vec, z_vec)
            return "Imported NK data from arrays."

        if kind == "nk_file":
            if not file_path:
                return "ERROR: file_path required."
            fd_instance.importnk(file_path, file_units, x0, y0, z0, reverse_index)
            return f"Imported NK from {file_path}."

        if kind == "rfile":
            result = fd_instance.rfile(file_path) if file_path else fd_instance.rfile()
            return str(result)

        if not file_path and kind not in ("rfile",):
            return "ERROR: file_path required."

        if kind == "mdf":
            fd_instance.loaddatafile(file_path, var) if var else fd_instance.loaddatafile(file_path)
        elif kind == "mat":
            fd_instance.loadmatlabmatfile(file_path, var) if var else fd_instance.loadmatlabmatfile(file_path)
        elif kind == "h5":
            fd_instance.loadh5file(file_path, var) if var else fd_instance.loadh5file(file_path)
        elif kind == "ascii":
            fd_instance.loadascii(file_path, var) if var else fd_instance.loadascii(file_path)
        elif kind == "readm":
            result = fd_instance.readm(file_path, size) if size is not None else fd_instance.readm(file_path)
            return f"readm: {result}"
        elif kind == "readascii":
            result = fd_instance.readascii(file_path, x) if x is not None else fd_instance.readascii(file_path)
            return f"readascii: {result}"
        elif kind == "readb":
            fd_instance.readb(file_path)
        elif kind == "readgraph":
            return f"readgraph: {fd_instance.readgraph(file_path)}"
        elif kind == "fread":
            if nitems is None or not type_name:
                return "ERROR: nitems and type_name required for fread."
            return str(fd_instance.fread(file_path, nitems, type_name, swapb))
        else:
            return f"ERROR: Unknown kind {kind!r}"

        return f"Loaded ({kind}) from '{file_path}'."
    except Exception as e:
        return f"ERROR: load_data({kind}) failed: {e}"


@mcp_instance.tool(title="Save data")
def save_data(
    kind: Annotated[SaveKind, Field(description="Save format: mdf / mat / h5 / ascii.")],
    file_path: Annotated[str, Field(description="Destination path.")],
    var_names: Annotated[Optional[list[str]], Field(description="Variables to save; omit = all (except h5 may require names).")] = None,
) -> str:
    """Save workspace variables to a file. Use project_action(save) to save the .sim project."""
    try:
        api = {
            "mdf": "savedatafile",
            "mat": "savematlabmatfile",
            "h5": "saveh5file",
            "ascii": "saveascii",
        }[kind]
        if var_names:
            args = ", ".join(var_names)
            fd_instance.eval(f'{api}("{file_path}",{args});')
            return f"Saved {var_names} to '{file_path}' ({kind})."
        if kind == "h5":
            return "ERROR: var_names required for h5."
        fd_instance.eval(f'{api}("{file_path}");')
        return f"Saved workspace to '{file_path}' ({kind})."
    except Exception as e:
        return f"ERROR: save_data({kind}) failed: {e}"


@mcp_instance.tool(title="File I/O")
def file_io(
    action: Annotated[FileIoAction, Field(description="Low-level file write operation.")],
    file_path: Annotated[Optional[str], Field(description="File path where applicable.")] = None,
    access_type: Annotated[Optional[str], Field(description="fopen access mode.")] = None,
    args: Annotated[Optional[list], Field(description="Objects list for writeascii.")] = None,
    type_name: Annotated[Optional[str], Field(description="fwrite type.")] = None,
    data: Annotated[Any, Field(description="fwrite data or write word / matrix var name.")] = None,
    sparse_format: Annotated[str, Field(description="spwrite format.")] = "sparse",
) -> str:
    """Low-level file open/close/write helpers."""
    try:
        if action == "fopen":
            if not file_path:
                return "ERROR: file_path required."
            fid = fd_instance.fopen(file_path, access_type) if access_type else fd_instance.fopen(file_path)
            return f"fopen ok, id={fid}"
        if action == "fclose":
            if not file_path:
                return "ERROR: file_path required."
            fd_instance.fclose(file_path)
            return f"Closed '{file_path}'."
        if action == "fwrite":
            if not file_path or not type_name:
                return "ERROR: file_path and type_name required."
            fd_instance.fwrite(file_path, type_name, data)
            return "fwrite ok."
        if action == "write":
            if not file_path:
                return "ERROR: file_path required."
            fd_instance.eval(f'write("{file_path}","{data}");')
            return "write ok."
        if action == "writem":
            if not file_path or data is None:
                return "ERROR: file_path and data (matrix var name) required."
            fd_instance.eval(f'writem("{file_path}", {data});')
            return "writem ok."
        if action == "writeascii":
            if not file_path or not args:
                return "ERROR: file_path and args (objects) required."
            objs = ", ".join(str(a) for a in args)
            fd_instance.eval(f'writeascii("{file_path}", {objs});')
            return "writeascii ok."
        if action == "spwrite":
            if not file_path or data is None:
                return "ERROR: file_path and data (sparse var) required."
            fd_instance.eval(f'spwrite("{file_path}", {data}, "{sparse_format}");')
            return "spwrite ok."
        return f"ERROR: Unknown action {action!r}"
    except Exception as e:
        return f"ERROR: file_io({action}) failed: {e}"
