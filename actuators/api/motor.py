from types import TracebackType
from typing import Callable, Literal, Optional, Protocol, Self

from .._utility import clip


type Bounds = tuple[float, float]
type BoundingFunction = Callable[[float, Optional[float]], float]


def clip_bound(bounds: Bounds) -> BoundingFunction:
    def bound(target: float, _: Optional[float]) -> float:
        return clip(target, minimum=bounds[0], maximum=bounds[1])

    return bound


def default_bound(target: float, _: Optional[float]) -> float:
    return target


class PositionMotor(Protocol):
    class Calibration(Protocol):
        kp: float
        kd: float
        gear: int
        direction: Literal[-1, 1]
        bound: BoundingFunction
        timeout: Optional[float]

    class Status(Protocol):
        position: float
        velocity: float
        torque: float

    calibration: Calibration
    last_status: Optional[Status]

    def __enter__(self: Self) -> Self: ...

    def __exit__(
        self: Self,
        exception_type: type[BaseException],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> None:
        ...

    def enable(self: Self) -> None: ...

    def disable(self: Self) -> None: ...

    def move(self: Self, position: float) -> None: ...

    def set_zero(self: Self) -> None: ...

    def status(self: Self) -> Status: ...
