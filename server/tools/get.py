"""Query helpers: properties, paths, sources, sweeps, homogeneity (enum)."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

import numpy as np
from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

GetKind = Literal[
    "property",
    "unit_scale",
    "selection_count",
    "work_path",
    "program_path",
    "parent_data",
    "has_data",
    "source_list",
    "homogeneity",
    "sweep_has_data",
    "sweep_data",
    "solver_data",
    "eme_analysis",
]


@mcp_instance.tool(title="Get info")
def get_info(
    kind: Annotated[GetKind, Field(description="What to query.")],
    name: Annotated[
        Optional[str],
        Field(description="Property name, parent data name, object name, sweep name, solver property, EME analysis parameter, etc."),
    ] = None,
    name2: Annotated[
        Optional[str],
        Field(description="Second name: data_name for has_data/sweep; dataset for sweep_data."),
    ] = None,
    name3: Annotated[
        Optional[str],
        Field(description="Third name for sweep_data: getsweepoptdata(sweep, name2, name3)."),
    ] = None,
    physical_quantity: Annotated[
        Optional[str],
        Field(description="For unit_scale: length | time | frequency."),
    ] = None,
    source_query: Annotated[
        Literal["all", "id", "name"],
        Field(description="For source_list."),
    ] = "all",
    monitor_name: Annotated[Optional[str], Field(description="For homogeneity.")] = None,
    index_0: Annotated[Optional[float], Field(description="Optional homogeneity reference index.")] = None,
    epsilon: Annotated[Optional[float], Field(description="Optional homogeneity tolerance.")] = None,
    variable_name: Annotated[str, Field(description="Workspace variable for sweep_data / solver_data.")] = "val",
) -> Any:
    """Discover properties and metadata. Prefer this before inventing property names for set.

    kind=eme_analysis calls getemeanalysis(name) for the EME Analysis Window
    (not object get). Pair with set_eme_analysis; sweep results use
    get_results(kind="eme_sweep").
    """
    try:
        if kind == "property":
            if not name:
                raw = fd_instance.get()
                if raw is None:
                    return []
                if isinstance(raw, np.ndarray):
                    if raw.size == 0:
                        return []
                    return [str(x).strip() for x in raw.flatten() if str(x).strip()]
                return []
            return fd_instance.get(name)

        if kind == "unit_scale":
            qty = physical_quantity or name
            if not qty:
                return "ERROR: physical_quantity required for unit_scale."
            scale = fd_instance.getunits(qty)
            return f"The scale factor for '{qty}' is: {scale}"

        if kind == "selection_count":
            return f"Number of selected objects: {fd_instance.getnumber()}"

        if kind == "work_path":
            return f"Current work path: {fd_instance.getworkpath()}"

        if kind == "program_path":
            return f"Program installation path: {fd_instance.getprogrampath()}"

        if kind == "parent_data":
            if not name:
                return "ERROR: name (data_name) required for parent_data."
            return fd_instance.getparentdata(name)

        if kind == "has_data":
            if name is None and name2 is None:
                return fd_instance.havedata()
            if not name or not name2:
                return "ERROR: name=object_name and name2=data_name required, or omit both to list."
            return fd_instance.havedata(name, name2)

        if kind == "source_list":
            if source_query == "all":
                return fd_instance.getsourcelist()
            return fd_instance.getsourcelist(source_query)

        if kind == "homogeneity":
            mon = monitor_name or name
            if not mon:
                return "ERROR: monitor_name required for homogeneity."
            if index_0 is None:
                return fd_instance.ishomogeneity(mon)
            if epsilon is None:
                return fd_instance.ishomogeneity(mon, index_0)
            return fd_instance.ishomogeneity(mon, index_0, epsilon)

        if kind == "sweep_has_data":
            if not name or not name2:
                return "ERROR: name=sweep_name and name2=data_name required."
            return fd_instance.havesweepoptdata(name, name2)

        if kind == "sweep_data":
            if not name:
                return "ERROR: name=sweep_name required."
            if name2 and name3:
                script = f'{variable_name} = getsweepoptdata("{name}", "{name2}", "{name3}");'
            elif name2:
                script = f'{variable_name} = getsweepoptdata("{name}", "{name2}");'
            else:
                script = f'{variable_name} = getsweepoptdata("{name}");'
            fd_instance.eval(script)
            return fd_instance.getv(variable_name)

        if kind == "solver_data":
            if not name:
                return "ERROR: name=property_name required for solver_data."
            script = f'{variable_name} = getsolverdata("{name}");'
            fd_instance.eval(script)
            return f"Solver data for '{name}': {fd_instance.getv(variable_name)}"

        if kind == "eme_analysis":
            if not name:
                return "ERROR: name=parameter required for eme_analysis (getemeanalysis)."
            return fd_instance.getemeanalysis(name)

        return f"ERROR: Unknown kind {kind!r}"
    except Exception as e:
        return f"ERROR: get_info({kind}) failed: {e}"
