from typing import Optional


def clip[T: int | float](
    value: T,
    minimum: Optional[T] = None,
    maximum: Optional[T] = None
) -> T:
    minimum = minimum if minimum is not None else value
    maximum = maximum if maximum is not None else value

    return min(max(value, minimum), maximum)
