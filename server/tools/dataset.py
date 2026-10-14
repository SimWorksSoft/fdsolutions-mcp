"""Dataset object parameter / attribute queries."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from pydantic import Field

from mcp_instance import mcp_instance

DatasetQuery = Literal["parameter", "attribute"]


@mcp_instance.tool(title="Dataset query")
def dataset_query(
    kind: Annotated[DatasetQuery, Field(description="parameter or attribute.")],
    dataset_obj: Annotated[Any, Field(description="Dataset object from get_results/dataset.")],
    name: Annotated[Optional[str], Field(description="Parameter/attribute name; omit to list.")] = None,
) -> Any:
    """Query parameters or attributes on a dataset object (not fd_instance)."""
    try:
        if kind == "parameter":
            return dataset_obj.getparameter() if name is None else dataset_obj.getparameter(name)
        return dataset_obj.getattribute() if name is None else dataset_obj.getattribute(name)
    except Exception as e:
        return f"ERROR: dataset_query({kind}) failed: {e}"
