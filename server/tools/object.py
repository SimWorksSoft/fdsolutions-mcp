"""Object selection and tree manipulation (enum ``action``)."""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

ObjectAction = Literal[
    "select",
    "select_partial",
    "shift_select",
    "shift_select_partial",
    "select_all",
    "unselect_all",
    "select_parent",
    "disable",
    "enable",
    "copy",
    "delete",
    "delete_all",
    "add_vertex",
    "delete_vertex",
]


@mcp_instance.tool(title="Object action")
def object_action(
    action: Annotated[
        ObjectAction,
        Field(
            description=(
                "select / select_partial / shift_select / shift_select_partial / "
                "select_all / unselect_all / select_parent / "
                "enable / disable / copy / delete / delete_all / "
                "add_vertex / delete_vertex. Prefer select/select_partial over re-adding. "
                "shift_* add to the current selection (same group only). "
                "Do not disable objects to work around a failed select."
            ),
        ),
    ],
    name: Annotated[
        Optional[str],
        Field(
            description=(
                "Select path rules (try in order; stop at first success): "
                "(1) Top-level objects: bare Name from add, e.g. 'Ring', 'FDTD', 'Bus_top'. "
                "(2) Nested under a solver: 'Solver::Object', e.g. 'FDTD::Index'. "
                "(3) Ports / objects under a port group under FDTD: "
                "'FDTD::PortGroupName::PortName', e.g. 'FDTD::Ports::Port_input' "
                "(NOT bare 'Port_input', NOT 'Ports::Port_input', NOT 'Port Group::...'). "
                "(4) select_partial / shift_select_partial: 'FDTD::Port' (all ports under FDTD), "
                "'::Ports' (port group), '::Child' / 'Parent::Child'. "
                "Bare child names and Group::Child without the solver prefix usually fail "
                "for ports. Remember Names from add / rename."
            ),
        ),
    ] = None,
    name2: Annotated[
        Optional[str],
        Field(
            description=(
                "Optional second arg for select / shift_select / select_partial / "
                "shift_select_partial. Same forms as select: select('name', value) or "
                "select('type', typeValue). Prefer full Solver::Group::Child paths for ports."
            ),
        ),
    ] = None,
    cord_1: Annotated[Optional[float], Field(description="Vertex coord 1 (SI m). For add_vertex.")] = None,
    cord_2: Annotated[Optional[float], Field(description="Vertex coord 2 (SI m). For add_vertex.")] = None,
    order_num: Annotated[Optional[int], Field(description="Vertex order for add_vertex / delete_vertex.")] = None,
    k: Annotated[int, Field(description="Selected polygon index (1 = uppermost).")] = 1,
) -> str:
    """Manipulate selection and objects in the project tree (SI meters for vertices).

    **Select cheat-sheet (SimWorks ``select`` / ``selectpartial`` / ``shiftselect*``):**
    - Structures at root: ``select('Ring')``.
    - Under FDTD: ``select('FDTD::MonitorName')``.
    - Mode ports: ``select('FDTD::Ports::Port_input')`` — include **solver + port
      group + port**. Omitting ``FDTD::`` is the usual reason select fails.
    - Discover group: ``select_partial('::Ports')`` or ``select_partial('FDTD::Port')``.
    - Multi-select: ``shift_select`` / ``shift_select_partial`` add without clearing
      (same group only); then ``set_property`` applies to all selected.
    - If select fails: retry with ``FDTD::<Group>::<Child>``; never re-add or disable.
    """
    try:
        if action == "select_all":
            fd_instance.selectall()
            return "All objects selected."
        if action == "unselect_all":
            fd_instance.unselectall()
            return "All objects unselected."
        if action == "select_parent":
            fd_instance.selectparent()
            return "Parent object selected."
        if action == "delete_all":
            fd_instance.deleteall()
            return "All objects deleted."
        if action == "select_partial":
            if not name:
                return "ERROR: name (partial pattern) is required for select_partial."
            if name2:
                fd_instance.selectpartial(name, name2)
            else:
                fd_instance.selectpartial(name)
            return f"Objects matching '{name}' selected."
        if action == "shift_select_partial":
            if name2:
                fd_instance.shiftselectpartial(name, name2)
            elif name:
                fd_instance.shiftselectpartial(name)
            else:
                fd_instance.shiftselectpartial()
            detail = f" matching '{name}'" if name else ""
            return f"Additive partial selection{detail} (shiftselectpartial)."
        if action == "select":
            if not name:
                return "ERROR: name is required for select."
            if name2:
                fd_instance.select(name, name2)
            else:
                fd_instance.select(name)
            return f"Selected '{name}'."
        if action == "shift_select":
            if name2:
                fd_instance.shiftselect(name, name2)
            elif name:
                fd_instance.shiftselect(name)
            else:
                fd_instance.shiftselect()
            detail = f" '{name}'" if name else ""
            return f"Added{detail} to selection (shiftselect)."
        if action == "add_vertex":
            if cord_1 is None or cord_2 is None or order_num is None:
                return "ERROR: cord_1, cord_2, order_num required for add_vertex."
            fd_instance.addvertex(cord_1, cord_2, order_num, k)
            return f"Vertex added at ({cord_1}, {cord_2}) on polygon index {k}."
        if action == "delete_vertex":
            if order_num is None:
                return "ERROR: order_num required for delete_vertex."
            fd_instance.delvertex(order_num, k)
            return f"Vertex {order_num + 1} deleted from polygon index {k}."

        # name-optional single-arg actions
        method = getattr(fd_instance, action if action != "delete" else "delete")
        if name:
            method(name)
            return f"{action} applied to '{name}'."
        method()
        return f"{action} applied to current selection."
    except Exception as e:
        hint = ""
        if action in ("select", "select_partial", "shift_select", "shift_select_partial"):
            hint = (
                " For ports use FDTD::<PortGroup>::<PortName> "
                "(e.g. FDTD::Ports::Port_input). Else try Solver::Object, "
                "select_partial('FDTD::Port') or '::Group'. "
                "shift_* only multi-select within the same group. "
                "Do not re-add or disable to bypass this."
            )
        return f"ERROR: object_action({action}) failed: {e}.{hint}"
