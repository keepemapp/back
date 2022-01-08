from fastapi.params import Query

from kpm.shared.domain.model import RootAggState

order_by = Query(
    None,
    max_length=20,
    regex=r"^[^;\-'\"]+$",
    description="Attribute to sort by",
)

order = Query(
    "asc",
    max_length=4,
    regex=r"^(asc|desc)$",
    description="Available options: 'asc', 'desc'",
)

state = Query(
    None,
    max_length=10,
    regex=rf"^({RootAggState.PENDING.value}|{RootAggState.ACTIVE.value})$",
    description="Available options: 'pending' or 'active'",
)
