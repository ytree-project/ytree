"""
YTreeArbor utilities



"""

_ops = {"above": ">=", "below": "<=", "equal": "=="}

def get_conditional(op, criterion):
    my_op = _ops[op]

    if len(criterion) == 2:
        field, value = criterion
        units = None
    elif len(criterion) == 3:
        field, value, units = criterion
    else:
        raise ValueError(
            "Criterion must have either two or three values: "
            f"{criterion}.")

    if units is None:
        ustr = ""
    else:
        ustr = f".in_units(\"{units}\")"

    condition = f"obj[\"halos\", \"{field}\"]{ustr} {my_op} {value}"
    return condition

def get_about(criterion):
    if len(criterion) == 3:
        field, value, within = criterion
        units = None
    elif len(criterion) == 4:
        field, value, units, within = criterion
    else:
        raise ValueError(
            "Criterion must have either two or three values: "
            f"{criterion}.")

    c1 = get_conditional("above", (field, (1-within)*value, units))
    c2 = get_conditional("below", (field, (1+within)*value, units))
    return [c1, c2]
