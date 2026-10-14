"""Property set, group configuration, source signal, and EME analysis-window set.

``set_property`` is write-only and SI-only for *selected objects*. Discover
valid names with ``get_info(kind="property")`` after a failed set — do not
unit-convert here.

``set_source_signal`` assigns a custom time-domain waveform to an existing
source (``setsourcesignal``) — not object ``set``.

``set_eme_analysis`` configures the EME Analysis Window via
``setemeanalysis`` — not object ``set``. Do not use ``set_property`` for
EME analysis parameters.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal, Optional

from pydantic import Field

from fd_instance import fd_instance
from mcp_instance import mcp_instance

# Number optionally followed by a unit token (ASCII letter / mu / CJK) → reject.
_NUMBER_WITH_UNIT_RE = re.compile(
    r"^[+-]?\d*\.?\d+(?:[eE][+-]?\d+)?\s*[a-zA-Zμ\u4e00-\u9fff]+$"
)


def _coerce_set_value(value: Any) -> Any:
    """Normalize value for fd_instance.set. Numbers must already be SI."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if value is None:
        raise ValueError("value is required.")

    if isinstance(value, str):
        text = value.strip()
        lower = text.lower()
        if lower in ("true", "false"):
            return lower == "true"
        if _NUMBER_WITH_UNIT_RE.match(text):
            raise ValueError(
                f"Refuse unit string {value!r}. Convert to SI yourself "
                "(meters, seconds, hertz) and pass a bare number, e.g. 1.5e-6 not '1.5 um'."
            )
        # Pure numeric string → number; otherwise keep as property string (material, enum, …).
        try:
            if re.fullmatch(r"[+-]?\d+", text):
                return int(text)
            if re.fullmatch(r"[+-]?\d*\.?\d+(?:[eE][+-]?\d+)?", text):
                return float(text)
        except ValueError:
            pass
        return text

    return value


@mcp_instance.tool(title="Set property")
def set_property(
    property_name: Annotated[str, Field(description="Exact SimWorks property name on the selected object.")],
    value: Annotated[
        Any,
        Field(
            description=(
                "New value. Numbers must be SI (m, s, Hz) with no unit suffix. "
                "Bool as true/false. Strings for materials/enums."
            ),
        ),
    ],
    k: Annotated[
        Optional[int],
        Field(description="Optional selection index when multiple objects are selected (1 = uppermost)."),
    ] = None,
) -> str:
    """Set one property on the currently selected object(s).

    Prefer calling directly when you know the exact SimWorks property name.
    Numbers are SI only. On failure, get_info(kind="property"), then retry only
    the failed property — do not invent names from similar software. If you set ``name``,
    remember the new name for later object_action select (use Parent::Child when nested).

    After a simulation finishes, many properties can only be set in **design**
    layout. If set fails with a design-layout / inactive message, call
    ``switch_layout(layout="design")`` (confirm first if results would be lost),
    then retry — do not re-add objects to work around this.
    """
    if not property_name or not str(property_name).strip():
        return "ERROR: property_name is required."

    try:
        target = _coerce_set_value(value)
        if k is not None:
            fd_instance.set(property_name, target, k)
        else:
            fd_instance.set(property_name, target)
        return f"[OK] set('{property_name}', {target!r})"
    except Exception as e:
        err = str(e)
        hint = (
            "Call get_info(kind='property') for valid names on the selection, "
            "then retry with the exact name and SI numeric values."
        )
        if any(
            s in err.lower()
            for s in ("design layout", "inactive", "switchtodesign", "run layout")
        ):
            hint = (
                "Property edits after a solve usually need switch_layout(layout='design') "
                "first (confirm with user if results will be discarded), then retry set. "
                "Do not re-add objects."
            )
        return f"ERROR: set('{property_name}', {value!r}) failed: {e}. {hint}"


# ---------------------------------------------------------------------------
# Group configuration
# ---------------------------------------------------------------------------

GroupMembershipAction = Literal["add_to_group", "remove_from_group"]
GroupVariableKind = Literal["setup", "parameter", "result"]
GroupVariableType = Literal[
    "number",
    "text",
    "length",
    "time",
    "frequency",
    "material",
    "global variable",
]


@mcp_instance.tool(title="Group membership")
def group_membership(
    action: Annotated[
        GroupMembershipAction,
        Field(description="add_to_group: move selection into group_name; remove_from_group: ungroup selection."),
    ],
    group_name: Annotated[
        Optional[str],
        Field(description="Target group name. Required when action is add_to_group."),
    ] = None,
) -> str:
    """Add the selected object to a group, or remove it from its current group."""
    try:
        if action == "add_to_group":
            if not group_name:
                return "ERROR: group_name is required when action is add_to_group."
            fd_instance.addtogroup(group_name)
            return f"Selected object successfully added to group '{group_name}'."
        fd_instance.removefromgroup()
        return "Selected object successfully removed from its group."
    except Exception as e:
        return f"ERROR: Failed group membership ({action}): {e}"


@mcp_instance.tool(title="Add group variable")
def add_group_variable(
    kind: Annotated[
        GroupVariableKind,
        Field(description="setup / parameter / result variable on the selected group."),
    ],
    value_name: Annotated[str, Field(description="Variable name.")],
    value_type: Annotated[
        Optional[GroupVariableType],
        Field(description="Required for setup/parameter. Numeric kinds use SI."),
    ] = None,
    value_data: Annotated[
        Any,
        Field(description="Value for setup/parameter. Ignored for result."),
    ] = None,
) -> str:
    """Configure a setup, parameter, or result variable on the selected group."""
    try:
        if kind == "result":
            fd_instance.addresultvariable(value_name)
            return f"Result variable '{value_name}' added successfully."

        if value_type is None:
            return "ERROR: value_type is required for setup/parameter variables."

        vt = value_type.lower()
        data = value_data
        if vt in ("number", "length", "time", "frequency"):
            data = _coerce_set_value(data)
            if isinstance(data, str):
                return f"ERROR: {vt} values must be SI numbers, got {value_data!r}."
        elif vt in ("text", "material", "global variable"):
            data = str(data)
        else:
            return f"ERROR: Invalid value_type '{value_type}'"

        if kind == "setup":
            fd_instance.addsetupvariable(value_name, value_type, data)
        else:
            fd_instance.addparametervariable(value_name, value_type, data)
        return f"{kind.capitalize()} variable '{value_name}' ({value_type}) = {data} added successfully."
    except Exception as e:
        return f"ERROR: Failed to add {kind} variable '{value_name}': {e}"


# ---------------------------------------------------------------------------
# Source time-domain signal
# ---------------------------------------------------------------------------


@mcp_instance.tool(title="Set source signal")
def set_source_signal(
    source_name: Annotated[
        str,
        Field(
            description=(
                "Existing source path, e.g. 'FDTD::plane'. Does not create a source — "
                "add + optionally rename first."
            ),
        ),
    ],
    t: Annotated[
        list[float],
        Field(description="Time samples in seconds (SI), same length as amplitude and phase."),
    ],
    amplitude: Annotated[
        list[float],
        Field(description="Amplitude envelope samples, same length as t."),
    ],
    phase: Annotated[
        list[float],
        Field(description="Phase samples (radians), same length as t."),
    ],
    fcentre: Annotated[
        Optional[float],
        Field(
            description=(
                "Optional center frequency in Hz (SI). If set with bandwidth, used for "
                "material fits, mesh, and source limits; otherwise estimated from the signal."
            ),
        ),
    ] = None,
    bandwidth: Annotated[
        Optional[float],
        Field(description="Optional bandwidth in Hz (SI). Use together with fcentre."),
    ] = None,
) -> str:
    """Assign a user-defined time-domain signal to an existing source (``setsourcesignal``).

    Used in FDTD / FDFD for custom pulses (modulated Gaussian, multi-peak, etc.).
    This is **not** ``set_property`` — ordinary wavelength / pulse settings still use
    ``set_property`` on the selected source.

    ``t``, ``amplitude``, and ``phase`` must be equal-length 1D vectors (SI: s, —, rad).
    Prefer starting ``t`` at 0 so the initial field is zero.
    """
    if not source_name or not str(source_name).strip():
        return "ERROR: source_name is required."
    if not t or not amplitude or not phase:
        return "ERROR: t, amplitude, and phase must be non-empty lists."
    n = len(t)
    if len(amplitude) != n or len(phase) != n:
        return (
            f"ERROR: t/amplitude/phase length mismatch "
            f"({n}, {len(amplitude)}, {len(phase)})."
        )
    if (fcentre is None) ^ (bandwidth is None):
        return "ERROR: provide both fcentre and bandwidth, or neither."

    try:
        if fcentre is not None and bandwidth is not None:
            fd_instance.setsourcesignal(
                source_name, t, amplitude, phase, fcentre, bandwidth
            )
            return (
                f"[OK] setsourcesignal('{source_name}', …, "
                f"fcentre={fcentre}, bandwidth={bandwidth}) n={n}"
            )
        fd_instance.setsourcesignal(source_name, t, amplitude, phase)
        return f"[OK] setsourcesignal('{source_name}', t/amp/phase) n={n}"
    except Exception as e:
        return (
            f"ERROR: setsourcesignal('{source_name}', …) failed: {e}. "
            "Source must already exist; use add then this tool. "
            "Vectors must be SI (s, Hz)."
        )


# ---------------------------------------------------------------------------
# EME Analysis Window
# ---------------------------------------------------------------------------


@mcp_instance.tool(title="Set EME analysis")
def set_eme_analysis(
    parameter: Annotated[
        str,
        Field(
            description=(
                "EME Analysis Window parameter name, e.g. 'start wavelength', "
                "'tolerance 1', 'energy conservation'. Not an object property name."
            ),
        ),
    ],
    value: Annotated[
        Any,
        Field(
            description=(
                "New value. Lengths/wavelengths in SI meters (e.g. 1.1e-6). "
                "No unit suffix. Bool as true/false."
            ),
        ),
    ],
) -> str:
    """Set one parameter on the EME Analysis Window (``setemeanalysis``).

    Use this before ``run_action(eme_sweep)`` / ``eme_propagate`` when you need
    to configure sweep type, wavelength range, cell group span, tolerances,
    energy conservation, etc.

    This is **not** ``set_property``: it does not touch the selected object and
    ``get_info(kind="property")`` will not list these names. Read back with
    ``get_info(kind="eme_analysis")``. After a sweep, fetch results with
    ``get_results(kind="eme_sweep")``.
    """
    if not parameter or not str(parameter).strip():
        return "ERROR: parameter is required."

    try:
        target = _coerce_set_value(value)
        fd_instance.setemeanalysis(parameter, target)
        return f"[OK] setemeanalysis('{parameter}', {target!r})"
    except Exception as e:
        return (
            f"ERROR: setemeanalysis('{parameter}', {value!r}) failed: {e}. "
            "Use EME Analysis Window parameter names (SI numbers), not object "
            "properties. Confirm with get_info(kind='eme_analysis')."
        )
