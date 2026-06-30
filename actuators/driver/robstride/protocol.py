from __future__ import annotations

import math
import struct
import time
import typing

from dataclasses import dataclass
from enum import IntEnum
from typing import Annotated, Literal, Optional, Union

import can

from annotated_types import Interval, MaxLen

from ..._utility import clip


__all__ = (
    "ControlRequest",
    "Data",
    "DeviceId",
    "DisableRequest",
    "EnableRequest",
    "GetDeviceIdRequest",
    "GetDeviceIdResponse",
    "Kd",
    "Kp",
    "CommunicationType",
    "Position",
    "ProtocolError",
    "Request",
    "Response",
    "SetZeroPositionRequest",
    "StatusRequest",
    "StatusResponse",
    "Torque",
    "UnknownCommunicationTypeError",
    "Velocity",

    "decode",
    "encode",
    "open",
    "read",
    "send",
    "write"
)


type _Extra = Annotated[int, Interval(ge=0x00, le=0xffff)]


class ProtocolError(Exception):
    pass


class UnknownCommunicationTypeError(ProtocolError):
    value: int

    def __init__(self, value: int) -> None:
        super().__init__()

        self.value = value


class CommunicationType(IntEnum):
    GET_DEVICE_ID = 0
    OPERATION_CONTROL = 1
    OPERATION_STATUS = 2
    ENABLE = 3
    DISABLE = 4
    SET_ZERO_POSITION = 6
    SET_DEVICE_ID = 7
    READ_PARAMETER = 17
    WRITE_PARAMETER = 18
    FAULT_REPORT = 21
    SAVE_PARAMETERS = 22
    SET_BAUDRATE = 23
    ACTIVE_REPORT = 24
    SET_PROTOCOL = 25


type Position = Annotated[
    float,
    Interval(ge=-4 * math.pi, le=4 * math.pi),
    "rad"
]


type Velocity = Annotated[float, Interval(ge=-44.0, le=44.0), "rad / s"]
type Torque = Annotated[float, Interval(ge=-17.0, le=17.0), "N * m"]
type Kp = Annotated[float, Interval(ge=0.0, le=500.0), "N * m / rad"]
type Kd = Annotated[float, Interval(ge=0.0, le=5.0), "N * m / (rad / s)"]


@dataclass(kw_only=True)
class GetDeviceIdRequest:
    communication_type: Literal[CommunicationType.GET_DEVICE_ID] = \
        CommunicationType.GET_DEVICE_ID


@dataclass(kw_only=True)
class ControlRequest:
    position: Position
    kp: Kp
    kd: Kd
    velocity: Velocity = 0.0
    torque: Torque = 0.0

    communication_type: Literal[CommunicationType.OPERATION_CONTROL] = \
        CommunicationType.OPERATION_CONTROL


@dataclass(kw_only=True)
class GetDeviceIdResponse:
    id: bytes

    communication_type: Literal[CommunicationType.GET_DEVICE_ID] = \
        CommunicationType.GET_DEVICE_ID


@dataclass(kw_only=True)
class StatusRequest:
    communication_type: Literal[CommunicationType.OPERATION_STATUS] = \
        CommunicationType.OPERATION_STATUS


@dataclass(kw_only=True)
class DisableRequest:
    communication_type: Literal[CommunicationType.DISABLE] = \
        CommunicationType.DISABLE


@dataclass(kw_only=True)
class EnableRequest:
    communication_type: Literal[CommunicationType.ENABLE] = \
        CommunicationType.ENABLE


@dataclass(kw_only=True)
class SetZeroPositionRequest:
    communication_type: Literal[CommunicationType.SET_ZERO_POSITION] = \
        CommunicationType.SET_ZERO_POSITION


@dataclass(kw_only=True)
class StatusResponse:
    mode: int
    uncalibrated: bool
    stall: bool
    magnetic_encoder_fault: bool
    overtemperature: bool
    overcurrent: bool
    undervoltage: bool

    position: Position
    velocity: Velocity
    torque: Torque
    temperature: float

    communication_type: Literal[CommunicationType.OPERATION_STATUS] = \
        CommunicationType.OPERATION_STATUS


type Request = Union[
    ControlRequest,
    DisableRequest,
    EnableRequest,
    GetDeviceIdRequest,
    SetZeroPositionRequest,
    StatusRequest
]


type Response = Union[
    GetDeviceIdResponse,
    StatusResponse
]


type Data = Annotated[bytes, MaxLen(8)]
type DeviceId = Annotated[int, Interval(gt=0x00, le=0xff)]


def _decode_float(value: int, interval: Interval) -> float:
    assert isinstance(interval.ge, float)
    assert isinstance(interval.le, float)

    if interval.ge < 0:
        result = ((float(value) / 0x7fff) - 1.0) * interval.le
    else:
        result = (float(value) / 0xffff) * interval.le
    
    return result


def _decode_get_id_response(data: Data, _: _Extra) -> GetDeviceIdResponse:
    return GetDeviceIdResponse(id=data)


def _decode_status_response(data: Data, extra: _Extra) -> StatusResponse:
    mode = (extra >> 14) & 0x03
    uncalibrated = bool((extra >> 13) & 0x01)
    stall = bool((extra >> 12) & 0x01)
    magnetic_encoder_fault = bool((extra >> 11) & 0x01)
    overtemperature = bool((extra >> 10) & 0x01)
    overcurrent = bool((extra >> 9) & 0x01)
    undervoltage = bool((extra >> 8) & 0x01)

    position, velocity, torque, temperature = struct.unpack(">HHHH", data)

    position_interval = typing.get_args(Position.__value__)[1]
    position = _decode_float(position, position_interval)

    velocity_interval = typing.get_args(Velocity.__value__)[1]
    velocity = _decode_float(velocity, velocity_interval)

    torque_interval = typing.get_args(Torque.__value__)[1]
    torque = _decode_float(torque, torque_interval)

    temperature = float(temperature) * 0.1

    return StatusResponse(
        mode=mode,
        uncalibrated=uncalibrated,
        stall=stall,
        magnetic_encoder_fault=magnetic_encoder_fault,
        overtemperature=overtemperature,
        overcurrent=overcurrent,
        undervoltage=undervoltage,
        position=position,
        velocity=velocity,
        torque=torque,
        temperature=temperature
    )



def _encode_float(value: float, interval: Interval) -> int:
    assert isinstance(interval.ge, float)
    assert isinstance(interval.le, float)

    result = clip(value, minimum=interval.ge, maximum=interval.le)

    if interval.ge < 0:
        result = ((result / interval.le) + 1.0) * 0x7fff
    else:
        result = ((result) / interval.le) * 0xffff

    result = int(result)
    result = clip(result, minimum=0x00, maximum=0xffff)

    return result


def _encode_control_request(request: ControlRequest) -> tuple[_Extra, Data]:
    position_interval = typing.get_args(Position.__value__)[1]
    position = _encode_float(request.position, position_interval)

    velocity_interval = typing.get_args(Velocity.__value__)[1]
    velocity = _encode_float(request.velocity, velocity_interval)

    torque_interval = typing.get_args(Torque.__value__)[1]
    torque = _encode_float(request.torque, torque_interval)

    kp_interval = typing.get_args(Kp.__value__)[1]
    kp = _encode_float(request.kp, kp_interval)

    kd_interval = typing.get_args(Kd.__value__)[1]
    kd = _encode_float(request.kd, kd_interval)

    data = struct.pack(">HHHH", position, velocity, kp, kd)

    return torque, data


def _encode_empty_request(source_id: DeviceId) -> tuple[_Extra, Data]:
    return source_id, b"\x00" * 8


def _encode_set_zero_position_request(
    source_id: DeviceId
) -> tuple[_Extra, Data]:
    return source_id, b"\x01\x00\x00\x00\x00\x00\x00\x00"


def decode(
    arbitration_id: int,
    data: Data
) -> tuple[DeviceId, DeviceId, Response]:
    communication_type = (arbitration_id >> 24) & 0x1f
    extra = (arbitration_id >> 8) & 0xffff
    source_id = extra & 0xff
    destination_id = arbitration_id & 0xff

    match communication_type:
        case CommunicationType.GET_DEVICE_ID:
            response = _decode_get_id_response(data, extra)
        case CommunicationType.OPERATION_STATUS:
            response = _decode_status_response(data, extra)
        case _:
            raise UnknownCommunicationTypeError(communication_type)

    return source_id, destination_id, response


def encode(
    source_id: DeviceId,
    destination_id: DeviceId,
    request: Request
) -> tuple[int, Data]:
    match request.communication_type:
        case (
            CommunicationType.GET_DEVICE_ID |
            CommunicationType.OPERATION_STATUS |
            CommunicationType.DISABLE |
            CommunicationType.ENABLE
        ):
            extra, data = _encode_empty_request(source_id)
        case CommunicationType.OPERATION_CONTROL:
            extra, data = _encode_control_request(request)
        case CommunicationType.SET_ZERO_POSITION:
            extra, data = _encode_set_zero_position_request(source_id)
        case _:
            raise NotImplementedError

    arbitration_id = (
        (request.communication_type << 24) |
        (extra << 8) |
        (destination_id)
    )

    return arbitration_id, data


def open(name: str = "can0", bitrate: int = 1000000) -> can.BusABC:
    return can.interface.Bus(
        interface="socketcan",
        channel=name,
        bitrate=bitrate
    )


def write(
    bus: can.BusABC,
    source_id: DeviceId,
    destination_id: DeviceId,
    request: Request
) -> None:
    arbitration_id, data = encode(source_id, destination_id, request)
    frame = can.Message(
        arbitration_id=arbitration_id,
        dlc=len(data),
        data=data,
        is_extended_id=True
    )

    bus.send(frame)


def read(
    bus: can.BusABC,
    timeout: Optional[float]
) -> tuple[DeviceId, DeviceId, Response]:
    remaining = timeout

    while True:
        start_time = time.time()
        frame = bus.recv(timeout=remaining)
        finish_time = time.time()

        if not frame:
            raise TimeoutError

        if frame.is_extended_id:
            # When a motor drops off and reconnects, it sends a frame with
            # a zero device ID. These frames are recognized as non-extended ID
            # frames.

            break

        if remaining is not None:
            remaining = max(remaining - (finish_time - start_time), 0.0)

    return decode(frame.arbitration_id, bytes(frame.data))


def send(
    bus: can.BusABC,
    source_id: DeviceId,
    destination_id: DeviceId,
    request: Request,
    timeout: Optional[float] = None
) -> tuple[DeviceId, DeviceId, Response]:
    write(bus, source_id, destination_id, request)
    response = read(bus, timeout=timeout)

    return response
