"""Camera / layout switching (enum)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

ViewKind = Literal["top", "bottom", "front", "back", "left", "right", "xy", "yz", "zx"]
LayoutKind = Literal["run", "design"]

_VIEW_API = {
    "top": "switchtotopview",
    "bottom": "switchtobottomview",
    "front": "switchtofrontview",
    "back": "switchtobackview",
    "left": "switchtoleftview",
    "right": "switchtorightview",
    "xy": "switchtoXYview",
    "yz": "switchtoZYview",  # engine API name is ZY
    "zx": "switchtoZXview",
}


@mcp_instance.tool(title="Switch view")
def switch_view(
    view: Annotated[ViewKind, Field(description="Camera/view plane: top/bottom/front/back/left/right/xy/yz/zx.")],
) -> str:
    """Switch the CAD camera or view plane."""
    try:
        getattr(fd_instance, _VIEW_API[view])()
        return f"Switched to {view} view."
    except Exception as e:
        return f"ERROR: Failed to switch to {view} view: {e}"


@mcp_instance.tool(title="Switch layout")
def switch_layout(
    layout: Annotated[
        LayoutKind,
        Field(
            description=(
                "run: analysis / results layout (after a finished simulation). "
                "design: edit geometry, materials, ports, wavelength points, mesh, etc. "
                "After simulation completes, call design BEFORE any set_property that "
                "changes the project — many edits fail in run layout. "
                "design may discard existing results: confirm with the user first if "
                "results exist and have not been extracted/saved."
            ),
        ),
    ],
) -> str:
    """Switch between run and design layout modes.

    Workflow: run simulation → (extract results) → switch_layout('design') before
    further edits → switch_layout('run') only when you need the run/results UI again.
    Never assume set_property works while still in run layout after a solve.
    """
    try:
        if layout == "run":
            fd_instance.switchtorun()
            return "Switched to run layout."
        fd_instance.switchtodesign()
        return (
            "Switched to design layout. "
            "You may now edit properties; prior unsaved results may be cleared."
        )
    except Exception as e:
        return f"ERROR: Failed to switch to {layout} layout: {e}"
