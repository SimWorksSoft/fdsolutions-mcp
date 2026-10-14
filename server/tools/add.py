"""Unified object creation: one ``add(kind=...)`` tool.

API names and signatures follow SimWorks docs:
https://simworks.net/knowledge-base/Script-Commands_setting-objects
Configure properties afterward with ``set_property``.

``planar_solid`` supports all ``addplanarsolid`` overloads, including
``(vertices, facets)`` and ``(x, y, z, vertices, facets)``.
"""

from __future__ import annotations

from typing import Annotated, Any, Callable, Literal, Optional

from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

# Kinds that accept optional (x_pos, y_pos, z_pos) in meters.
# Kinds without position use API with no coordinate args.
AddKind = Literal[
    # structures
    "polygon",
    "triangle",
    "rectangle",
    "circle",
    "ellipse",
    "sector",
    "circular_ring",
    "elliptic_ring",
    "sphere",
    "pyramid",
    "cone",
    "linear_waveguide",
    "arc_waveguide",
    "linear_taper",
    "sidewall_linear",
    "sidewall_arc",
    "sidewall_bezier",
    "2d_rectangle",
    "2d_polygon",
    "photonic_crystal",
    "planar_solid",
    "equation",
    "import_nk",
    # groups
    "group",
    "structure_group",
    "assembly_group",
    "analysis_group",
    # library object (addobject)
    "library_object",
    # sources / ports
    "dipole",
    "plane",
    "tfsf",
    "mode_source",
    "gaussian",
    "import_source",
    "port_group",
    "mode_port",
    "eme_port",
    "import_generation",
    # monitors
    "power_monitor",
    "field_monitor",
    "time_monitor",
    "index_monitor",
    "eme_profile",
    "eme_index",
    # solvers / mesh (used in product; not all listed on setting-objects page)
    "fdtd",
    "fde",
    "fdfd",
    "eme",
    "rcwa",
    "fdcharge",
    "mesh",
]

# kind -> (api method, accepts_xyz)
# Docs: addemeport / addportgroup / addimportgeneration take NO coordinates.
# Docs: addmodeport may take (x,y,z); addemeport does not.
_ADD_API: dict[str, tuple[str, bool]] = {
    "polygon": ("addpoly", True),
    "triangle": ("addtriangle", True),
    "rectangle": ("addrect", True),
    "circle": ("addcircle", True),
    "ellipse": ("addellipse", True),
    "sector": ("addsector", True),
    "circular_ring": ("addcirclering", True),
    "elliptic_ring": ("addellipsering", True),
    "sphere": ("addsphere", True),
    "pyramid": ("addpyramid", True),
    "cone": ("addcone", True),
    "linear_waveguide": ("addlinearwaveguide", True),
    "arc_waveguide": ("addarcwaveguide", True),
    "linear_taper": ("addlineartaper", True),
    "sidewall_linear": ("addsidewalllinear", True),
    "sidewall_arc": ("addsidewallarc", True),
    "sidewall_bezier": ("addsidewallbezier", True),
    "2d_rectangle": ("add2drect", True),
    "2d_polygon": ("add2dpolygon", True),
    "photonic_crystal": ("addphotoniccrystal", True),
    "planar_solid": ("addplanarsolid", True),
    "equation": ("addequation", True),
    "import_nk": ("addimportnk", True),
    "group": ("addgroup", True),
    "structure_group": ("addstructuregroup", True),
    "assembly_group": ("addassemblygroup", True),
    "analysis_group": ("addanalysisgroup", True),
    "library_object": ("addobject", False),
    "dipole": ("adddipole", True),
    "plane": ("addplane", True),
    "tfsf": ("addtfsf", True),
    "mode_source": ("addmodesource", True),
    "gaussian": ("addgaussiansource", True),
    "import_source": ("addimportsource", True),
    "port_group": ("addportgroup", False),
    "mode_port": ("addmodeport", True),
    "eme_port": ("addemeport", False),
    "import_generation": ("addimportgeneration", False),
    "power_monitor": ("addpowermonitor", True),
    "field_monitor": ("addfieldmonitor", True),
    "time_monitor": ("addtimemonitor", True),
    "index_monitor": ("addindexmonitor", True),
    "eme_profile": ("addemeprofile", True),
    "eme_index": ("addemeindex", True),
    "fdtd": ("addfdtd", True),
    "fde": ("addfde", True),
    "fdfd": ("addfdfd", True),
    "eme": ("addeme", True),
    "rcwa": ("addrcwa", True),
    "fdcharge": ("addfdcharge", True),
    "mesh": ("addmesh", True),
}


def _label(kind: str) -> str:
    return kind.replace("_", " ")


def _coords_complete(
    x_pos: Optional[float], y_pos: Optional[float], z_pos: Optional[float]
) -> tuple[bool, bool]:
    """Return (any_given, all_given) for optional xyz."""
    coords = (x_pos, y_pos, z_pos)
    return any(c is not None for c in coords), all(c is not None for c in coords)


def _added_name_msg(label: str, detail: str) -> str:
    try:
        name = fd_instance.get("name")
        return f"{label} added {detail}. Name='{name}'."
    except Exception:
        return f"{label} added {detail}."


def _add_planar_solid(
    x_pos: Optional[float],
    y_pos: Optional[float],
    z_pos: Optional[float],
    vertices: Optional[list[list[float]]],
    facets: Optional[list],
) -> str:
    """Docs: addplanarsolid; (x,y,z); (vertices,facets); (x,y,z,vertices,facets)."""
    label = "planar solid"
    has_mesh = vertices is not None or facets is not None
    if has_mesh and (vertices is None or facets is None):
        return "ERROR: planar_solid custom mesh needs both vertices and facets."

    any_xyz, all_xyz = _coords_complete(x_pos, y_pos, z_pos)
    if any_xyz and not all_xyz:
        return (
            "ERROR: Provide all of x_pos, y_pos, z_pos (SI meters), "
            "or omit all three."
        )

    if has_mesh and all_xyz:
        fd_instance.addplanarsolid(x_pos, y_pos, z_pos, vertices, facets)
        return _added_name_msg(
            label, f"at ({x_pos:.2e}, {y_pos:.2e}, {z_pos:.2e}) with custom mesh"
        )
    if has_mesh:
        fd_instance.addplanarsolid(vertices, facets)
        return _added_name_msg(label, "with custom mesh (origin)")
    if all_xyz:
        fd_instance.addplanarsolid(x_pos, y_pos, z_pos)
        return _added_name_msg(label, f"at ({x_pos:.2e}, {y_pos:.2e}, {z_pos:.2e})")

    fd_instance.addplanarsolid()
    return _added_name_msg(label, "(default rectangle at origin)")


@mcp_instance.tool(title="Add object")
def add(
    kind: Annotated[
        AddKind,
        Field(
            description=(
                "Object to add (SimWorks script add* commands). "
                "Structures: polygon, triangle, rectangle, circle, ellipse, sector, "
                "circular_ring, elliptic_ring, sphere, pyramid, cone, linear_waveguide, "
                "arc_waveguide, linear_taper, sidewall_linear, sidewall_arc, "
                "sidewall_bezier, 2d_rectangle, 2d_polygon, photonic_crystal, "
                "planar_solid, equation, import_nk. "
                "planar_solid: optional vertices+facets for custom mesh "
                "(addplanarsolid overloads); otherwise default rectangle. "
                "Groups: group, structure_group, assembly_group, analysis_group. "
                "library_object: addobject from built-in library (needs script_id; "
                "omit script_id to list library ids). "
                "Sources: dipole, plane, tfsf, mode_source, gaussian, import_source, "
                "port_group, mode_port, eme_port, import_generation. "
                "Monitors: power_monitor, field_monitor, time_monitor, index_monitor, "
                "eme_profile, eme_index. "
                "Solvers/mesh: fdtd, fde, fdfd, eme, rcwa, fdcharge, mesh. "
                "Creation only — configure with set_property. Positions are SI meters. "
                "port_group / eme_port / import_generation take no coordinates. "
                "mode_port needs an active port group; eme_port needs an active EME port group; "
                "import_generation needs an existing fdcharge solver. "
                "Do not re-add an existing object; remember the Name returned by add."
            ),
        ),
    ],
    x_pos: Annotated[
        Optional[float],
        Field(description="Center x in meters (SI). Omit with y/z to use API default (no-arg add*)."),
    ] = None,
    y_pos: Annotated[
        Optional[float],
        Field(description="Center y in meters (SI)."),
    ] = None,
    z_pos: Annotated[
        Optional[float],
        Field(description="Center z in meters (SI)."),
    ] = None,
    script_id: Annotated[
        Optional[str],
        Field(description="For kind=library_object: library script id. Omit to list available objects."),
    ] = None,
    vertices: Annotated[
        Optional[list[list[float]]],
        Field(
            description=(
                "For kind=planar_solid only: Nx3 vertex matrix in meters, "
                "each row [x, y, z]. Must be paired with facets."
            ),
        ),
    ] = None,
    facets: Annotated[
        Optional[list],
        Field(
            description=(
                "For kind=planar_solid only: face list; each face is vertex indices "
                "(1-based, right-hand rule), e.g. [[1,4,3,2],[1,5,8,4],...]. "
                "Must be paired with vertices."
            ),
        ),
    ] = None,
) -> str:
    """Add a simulation object (SimWorks add* only; configure with set_property).

    After success, the reply includes ``Name='...'``. Record that exact name for
    later select / set / delete. Do not call add again for an object that already
    exists (especially port_group, mode_port, fdtd) — if select fails, use
    object_action path forms instead of re-adding.
    Docs: https://simworks.net/knowledge-base/Script-Commands_setting-objects
    """
    api_name, accepts_xyz = _ADD_API[kind]
    label = _label(kind)

    try:
        if vertices is not None or facets is not None:
            if kind != "planar_solid":
                return "ERROR: vertices/facets are only valid for kind=planar_solid."

        # --- library object (addobject) ---
        if kind == "library_object":
            if script_id:
                fd_instance.addobject(script_id)
                return f"Library object '{script_id}' added."
            listing = fd_instance.addobject()
            return f"Available library objects: {listing}"

        # --- planar solid (docs: 4 overloads including vertices/facets) ---
        if kind == "planar_solid":
            return _add_planar_solid(x_pos, y_pos, z_pos, vertices, facets)

        method: Callable[..., Any] = getattr(fd_instance, api_name)

        if not accepts_xyz:
            method()
            # Some no-arg adds still select the new object with a name
            try:
                name = fd_instance.get("name")
                return f"{label} added successfully. Name='{name}'."
            except Exception:
                return f"{label} added successfully."

        # Position optional: docs allow addrect; or addrect(x,y,z);
        any_xyz, all_xyz = _coords_complete(x_pos, y_pos, z_pos)
        if not any_xyz:
            method()
            name = fd_instance.get("name")
            return f"{label} added (default position). Name='{name}'."

        if not all_xyz:
            return (
                "ERROR: Provide all of x_pos, y_pos, z_pos (SI meters), "
                "or omit all three for the no-argument form."
            )

        method(x_pos, y_pos, z_pos)
        name = fd_instance.get("name")
        return (
            f"{label} added at ({x_pos:.2e}, {y_pos:.2e}, {z_pos:.2e}). "
            f"Name='{name}'."
        )
    except Exception as e:
        return f"ERROR: Failed to add {label}: {e}"
