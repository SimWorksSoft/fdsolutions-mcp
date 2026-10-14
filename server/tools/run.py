"""Run / solve actions (enum)."""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

RunAction = Literal[
    "run",
    "status",
    "solve_mode",
    "run_setup",
    "run_analysis",
    "eme_propagate",
    "run_sweep",
    "eme_sweep",
    "resource_info",
]

EmeSweepMode = Literal[
    "propagation sweep",
    "wavelength sweep",
    "mode convergence sweep",
]


@mcp_instance.tool(title="Run / solve")
def run_action(
    action: Annotated[
        RunAction,
        Field(
            description=(
                "run: launch simulation (confirm with user first). "
                "status: poll FDTD simulation status (use after run / timeout). "
                "solve_mode: FDE mode solve. "
                "run_setup: structure-group setup script. "
                "run_analysis: analysis-group script. "
                "eme_propagate: EME propagation. "
                "run_sweep: runsweep — all sweeps, or named sweep via object_name "
                "(confirm first; long-running). "
                "eme_sweep: emesweep — optional eme_sweep_mode "
                "(propagation / wavelength / mode convergence); confirm first. "
                "resource_info: getresourceinfo — CPU/GPU resource listing. "
                "IMPORTANT: an MCP/client timeout on run / run_sweep / eme_sweep does "
                "NOT mean the job failed to start — do NOT call the same action again. "
                "Poll status when applicable. Only re-run if the user explicitly asks."
            ),
        ),
    ],
    object_name: Annotated[
        Optional[str],
        Field(
            description=(
                "Optional target: solve_mode / run_analysis object path; "
                "run_sweep sweep name (omit = all sweeps)."
            ),
        ),
    ] = None,
    eme_sweep_mode: Annotated[
        Optional[EmeSweepMode],
        Field(
            description=(
                "For action=eme_sweep only. Omit or 'propagation sweep' for default; "
                "'wavelength sweep'; 'mode convergence sweep'."
            ),
        ),
    ] = None,
) -> str:
    """Run solvers, sweeps, or analysis scripts.

    Confirm with the user before action=run / run_sweep / eme_sweep. If the call
    blocks until done and the MCP request times out, the solver may still be
    running in SimWorks — do not issue a second start to \"retry\" a timeout.
    """
    try:
        if action == "run":
            fd_instance.run()
            return "Simulation completed."
        if action == "status":
            status = fd_instance.getdata("FDTD", "simulation status")
            return (
                f"Simulation status: {status}. "
                "If a prior run MCP-timed-out, keep polling status — do not run again."
            )
        if action == "solve_mode":
            if object_name:
                fd_instance.solvemode(object_name)
            else:
                fd_instance.solvemode()
            return "Mode solve completed."
        if action == "run_setup":
            fd_instance.runsetup()
            return "Structure group setup script completed."
        if action == "run_analysis":
            if object_name:
                fd_instance.runanalysis(object_name)
            else:
                fd_instance.runanalysis()
            return "Analysis script completed."
        if action == "eme_propagate":
            fd_instance.emepropagate()
            return "EME propagation completed."
        if action == "run_sweep":
            if object_name:
                fd_instance.runsweep(object_name)
                return f"Sweep '{object_name}' completed."
            fd_instance.runsweep()
            return "All parameter sweeps completed."
        if action == "eme_sweep":
            if eme_sweep_mode:
                fd_instance.emesweep(eme_sweep_mode)
                return f"EME {eme_sweep_mode} completed."
            fd_instance.emesweep()
            return "EME propagation sweep completed."
        if action == "resource_info":
            return str(fd_instance.getresourceinfo())
        return f"ERROR: Unknown action {action!r}"
    except Exception as e:
        return f"ERROR: run_action({action}) failed: {e}"
