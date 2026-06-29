from dataclasses import dataclass
from typing import Literal, Optional, Self

import can

from ...api import motor as api
from . import protocol


class PositionMotor:
    @dataclass(kw_only=True)
    class Calibration:
        kp: protocol.Kp
        kd: protocol.Kd
        gear: int = 1
        direction: Literal[-1, 1] = 1
        bound: api.BoundingFunction = api.default_bound
        timeout: Optional[float] = 0.01

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
        self._calibration = calibration
        self._last_status = None

    def _send(self: Self, request: protocol.Request) -> protocol.Response:
        _, _, response = protocol.send(
            self._bus,
            self._source_id,
            self._destination_id,
            request,
            timeout=self._calibration.timeout
        )

        return response

    def _process(
        self: Self,
        request: protocol.Request
    ) -> api.PositionMotor.Status:
        response = self._send(request)

        assert isinstance(response, protocol.StatusResponse)

        response.position = (
            response.position *
            self._calibration.direction /
            self._calibration.gear
        )

        response.velocity = (
            response.position *
            self._calibration.direction /
            self._calibration.gear
        )

        response.torque = (
            response.torque *
            self._calibration.direction *
            self._calibration.gear
        )

        self._last_status = response

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
        position = (
            position * self._calibration.gear * self._calibration.direction
        )

        position = self._calibration.bound(
            position,
            self._last_status.position if self._last_status else None
        )

        self._process(
            protocol.ControlRequest(
                position=position,
                kp=self._calibration.kp,
                kd=self._calibration.kd,
                velocity=0.0,
                torque=0.0
            )
        )
