"""Job queue management (enum ``action``)."""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

JobAction = Literal["add", "list", "clear", "run"]


@mcp_instance.tool(title="Jobs")
def jobs_action(
    action: Annotated[JobAction, Field(description="add / list / clear / run job queue.")],
    file_path: Annotated[Optional[str], Field(description="Project file for add.")] = None,
    solver_type: Annotated[Optional[str], Field(description="Solver filter / type.")] = None,
    parallel_mode: Annotated[int, Field(description="Parallel mode for run (default 0).")] = 0,
) -> str:
    """Manage the simulation job queue."""
    try:
        if action == "add":
            if not file_path or not solver_type:
                return "ERROR: file_path and solver_type required for add."
            fd_instance.addjob(file_path, solver_type)
            return f"Job added: {file_path} ({solver_type})."
        if action == "list":
            result = fd_instance.listjobs(solver_type) if solver_type else fd_instance.listjobs()
            return str(result)
        if action == "clear":
            if solver_type:
                fd_instance.clearjobs(solver_type)
            else:
                fd_instance.clearjobs()
            return "Job queue cleared."
        if action == "run":
            if solver_type:
                fd_instance.runjobs(solver_type, parallel_mode)
            else:
                fd_instance.runjobs(parallel_mode)
            return "Jobs started."
        return f"ERROR: Unknown action {action!r}"
    except Exception as e:
        return f"ERROR: jobs_action({action}) failed: {e}"
