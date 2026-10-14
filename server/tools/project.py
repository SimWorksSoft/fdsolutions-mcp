"""Project open/save/new (enum)."""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

ProjectAction = Literal["open", "save", "new"]


@mcp_instance.tool(title="Project")
def project_action(
    action: Annotated[
        ProjectAction,
        Field(description="open / save / new project."),
    ],
    path: Annotated[
        Optional[str],
        Field(description="File path. Required for open; optional for save (omit = save current)."),
    ] = None,
) -> str:
    """Open, save, or create a simulation project. Prefer absolute paths."""
    try:
        if action == "open":
            if not path:
                return "ERROR: path is required for open."
            fd_instance.loadproject(path)
            return f"{path} has been opened."
        if action == "save":
            if path:
                fd_instance.saveproject(path)
                return f"Project saved to '{path}'."
            fd_instance.saveproject()
            return "Current project saved."
        if action == "new":
            fd_instance.newproject()
            return "New project created."
        return f"ERROR: Unknown action {action!r}"
    except Exception as e:
        return f"ERROR: project_action({action}) failed: {e}"
