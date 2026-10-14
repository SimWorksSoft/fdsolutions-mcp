"""Simulation results extraction (enum ``kind``)."""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

ResultKind = Literal[
    "data",
    "raw",
    "dataset",
    "electric",
    "magnetic",
    "dipole_power",
    "source_power",
    "source_intensity",
    "source_norm",
    "update_index_monitor",
    "monitor_to_dataset",
    "eme_sweep",
]


@mcp_instance.tool(title="Get results")
def get_results(
    kind: Annotated[ResultKind, Field(description="Result extraction mode.")],
    object_name: Annotated[Optional[str], Field(description="Object path, e.g. Solver::Monitor.")] = None,
    dataset_name: Annotated[Optional[str], Field(description="Dataset inside object (E, H, T, …).")] = None,
    data_name: Annotated[Optional[str], Field(description="Component inside dataset (Ex, …).")] = None,
    id_val: Annotated[Optional[int], Field(description="Object id alternative to object_name.")] = None,
    monitor_name: Annotated[Optional[str], Field(description="Monitor name for field/power helpers.")] = None,
    source_name: Annotated[Optional[str], Field(description="Optional source filter.")] = None,
    wavelength: Annotated[Optional[float], Field(description="Wavelength in meters (dipole_power).")] = None,
    wavelength_list: Annotated[Optional[list], Field(description="Wavelength list in meters.")] = None,
    variable_name: Annotated[str, Field(description="Workspace variable to store result.")] = "data",
) -> str:
    """
    Extract simulation results. For kind=data, call with no dataset/data first (LIST MODE)
    to discover available names, then call again with object_name + dataset_name [+ data_name].

    kind=eme_sweep: getemesweep(dataset_name) after run_action(eme_sweep).
    Configure the analysis window with set_eme_analysis / get_info(eme_analysis).
    """
    try:
        if kind == "data":
            if dataset_name is None and data_name is None:
                script = f"{variable_name} = getdata();"
            elif id_val is not None and dataset_name is not None and data_name is not None:
                script = f'{variable_name} = getdata({id_val}, "{dataset_name}", "{data_name}");'
            elif id_val is not None and dataset_name is not None and data_name is None:
                script = f'{variable_name} = getdata({id_val}, "{dataset_name}");'
            elif object_name is not None and dataset_name is not None and data_name is not None:
                script = f'{variable_name} = getdata("{object_name}", "{dataset_name}", "{data_name}");'
            elif object_name is not None and dataset_name is not None and data_name is None:
                script = f'{variable_name} = getdata("{object_name}", "{dataset_name}");'
            else:
                return (
                    "ERROR: Invalid getdata combination. Use list mode, or "
                    "object/id + dataset_name [, data_name]."
                )
            fd_instance.eval(script)
            return str(fd_instance.getv(variable_name))

        if kind == "raw":
            if object_name and data_name:
                script = f'{variable_name} = getrawdata("{object_name}", "{data_name}");'
            else:
                script = f"{variable_name} = getrawdata();"
            fd_instance.eval(script)
            return str(fd_instance.getv(variable_name))

        if kind == "dataset":
            if not object_name or not dataset_name:
                return "ERROR: object_name and dataset_name required for dataset."
            script = f'{variable_name} = getdataset("{object_name}", "{dataset_name}");'
            fd_instance.eval(script)
            return (
                f"Retrieved dataset '{dataset_name}' from '{object_name}' into '{variable_name}': "
                f"{fd_instance.getv(variable_name)}"
            )

        mon = monitor_name or object_name
        if kind == "electric":
            if not mon:
                return "ERROR: monitor_name required."
            script = f'{variable_name} = getelectric("{mon}");'
            fd_instance.eval(script)
            return f"|E|^2 from '{mon}': {fd_instance.getv(variable_name)}"

        if kind == "magnetic":
            if not mon:
                return "ERROR: monitor_name required."
            script = f'{variable_name} = getmagnetic("{mon}");'
            fd_instance.eval(script)
            return f"|H|^2 from '{mon}': {fd_instance.getv(variable_name)}"

        if kind == "dipole_power":
            if wavelength is None:
                return "ERROR: wavelength (SI m) required for dipole_power."
            if source_name:
                script = f'{variable_name} = getdipolepower({wavelength}, "{source_name}");'
            else:
                script = f"{variable_name} = getdipolepower({wavelength});"
            fd_instance.eval(script)
            return f"Dipole power: {fd_instance.getv(variable_name)}"

        if kind in ("source_power", "source_intensity", "source_norm"):
            if wavelength_list is None:
                return "ERROR: wavelength_list required."
            api = {
                "source_power": "getsourcepower",
                "source_intensity": "getsourceintensity",
                "source_norm": "getsourcenorm",
            }[kind]
            if source_name:
                script = f'{variable_name} = {api}({wavelength_list}, "{source_name}");'
            else:
                script = f"{variable_name} = {api}({wavelength_list});"
            fd_instance.eval(script)
            return f"{kind}: {fd_instance.getv(variable_name)}"

        if kind == "update_index_monitor":
            if not mon:
                return "ERROR: monitor_name required."
            fd_instance.updateindexmonitor(mon)
            return f"Updated index monitor '{mon}'."

        if kind == "monitor_to_dataset":
            if not mon:
                return "ERROR: monitor_name required."
            fd_instance.addmonitor2dataset(mon)
            return f"Extracted field data from '{mon}' into a dataset."

        if kind == "eme_sweep":
            ds = dataset_name
            if not ds:
                return (
                    "ERROR: dataset_name required for eme_sweep "
                    "(e.g. 'S', 'S_wavelength_sweep')."
                )
            script = f'{variable_name} = getemesweep("{ds}");'
            fd_instance.eval(script)
            return (
                f"EME sweep dataset '{ds}' -> '{variable_name}': "
                f"{fd_instance.getv(variable_name)}"
            )

        return f"ERROR: Unknown kind {kind!r}"
    except Exception as e:
        return f"ERROR: get_results({kind}) failed: {e}"
