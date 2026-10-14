"""Material library operations (enum ``action``)."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

MaterialAction = Literal[
    "list_models",
    "add",
    "set",
    "list_library",
    "list_properties",
    "get_property",
    "get_model",
]


@mcp_instance.tool(title="Material")
def material_action(
    action: Annotated[MaterialAction, Field(description="Material library operation.")],
    model_name: Annotated[Optional[str], Field(description="Material model type when adding.")] = None,
    material_name: Annotated[Optional[str], Field(description="Material name in library.")] = None,
    property_name: Annotated[Optional[str], Field(description="Property name for set/get.")] = None,
    property_value: Annotated[Any, Field(description="Value for set.")] = None,
    wavelength: Annotated[Optional[float], Field(description="Wavelength in meters for get_model.")] = None,
    data_type: Annotated[int, Field(description="get_model data_type (default 0).")] = 0,
) -> str:
    """List, add, set, or query materials. Do not invent material names — list first if unsure."""
    try:
        if action == "list_models":
            return str(fd_instance.addmaterial())
        if action == "add":
            if not model_name or not material_name:
                return "ERROR: model_name and material_name required for add."
            fd_instance.addmaterial(model_name, material_name)
            return f"Material '{material_name}' ({model_name}) added to library."
        if action == "set":
            if not material_name or not property_name:
                return "ERROR: material_name and property_name required for set."
            fd_instance.setmaterial(material_name, property_name, property_value)
            return f"Set {material_name}.{property_name} = {property_value}."
        if action == "list_library":
            return str(fd_instance.setmaterial())
        if action == "list_properties":
            if not material_name:
                return "ERROR: material_name required for list_properties."
            return str(fd_instance.setmaterial(material_name))
        if action == "get_property":
            if not material_name or not property_name:
                return "ERROR: material_name and property_name required for get_property."
            return str(fd_instance.getmaterial(material_name, property_name))
        if action == "get_model":
            if not material_name or wavelength is None:
                return "ERROR: material_name and wavelength required for get_model."
            return str(fd_instance.getmaterialmodel(material_name, wavelength, data_type))
        return f"ERROR: Unknown action {action!r}"
    except Exception as e:
        return f"ERROR: material_action({action}) failed: {e}"
