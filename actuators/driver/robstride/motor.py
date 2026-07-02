from dataclasses import dataclass
from typing import Literal, Optional, Self

import can

from ...api import motor as api
from . import protocol


__all__ = (
    "PositionMotor",
)


class PositionMotor(api.PositionMotor):
    @dataclass(kw_only=True)
    class Calibration:
        kp: protocol.Kp
        kd: protocol.Kd
        gear: int = 1
        direction: Literal[-1, 1] = 1
        bound: api.BoundingFunction = api.default_bound
        timeout: Optional[float] = 0.1

    def __init__(
        self: Self,
        bus: can.BusABC,
        destination_id: protocol.DeviceId,
        calibration: Calibration,
        source_id: protocol.DeviceId = 0xff
    ) -> None:
        self._bus = bus
        self._source_id = source_id
        self._destination_id = destination_id

        self.calibration = calibration
        self.last_status = None

    def _send(
        self: Self,
        request: protocol.Request,
        filter: protocol.ReadFilter = {}
    ) -> protocol.Response:
        filter = filter.copy()

        filter["source_id"] = self._destination_id

        _, _, response = protocol.send(
            self._bus,
            self._source_id,
            self._destination_id,
            request,
            filter=filter,
            timeout=self.calibration.timeout
        )

        return response

    def _process(
        self: Self,
        request: protocol.Request
    ) -> api.PositionMotor.Status:
        response = self._send(
            request,
            filter={
                "response_type": protocol.StatusResponse
            }
        )

        assert isinstance(response, protocol.StatusResponse)

        response.position = (
            response.position *
            self.calibration.direction /
            self.calibration.gear
        )

        response.velocity = (
            response.velocity *
            self.calibration.direction /
            self.calibration.gear
        )

        response.torque = (
            response.torque *
            self.calibration.direction *
            self.calibration.gear
        )

        self.last_status = response

        return response

    def enable(self: Self) -> None:
        self._process(protocol.EnableRequest())

    def disable(self: Self) -> None:
        self._process(protocol.DisableRequest())

    def zero(self: Self) -> None:
        self._process(protocol.SetZeroPositionRequest())

    def status(self: Self) -> api.PositionMotor.Status:
        return self._process(protocol.StatusRequest())

    def move(self: Self, position: float) -> None:
        position = self.calibration.bound(
            position,
            self.last_status.position if self.last_status else None
        )

        position = (
            position * self.calibration.gear * self.calibration.direction
        )

        self._process(
            protocol.ControlRequest(
                position=position,
                kp=self.calibration.kp,
                kd=self.calibration.kd,
                velocity=0.0,
                torque=0.0
            )
        )
