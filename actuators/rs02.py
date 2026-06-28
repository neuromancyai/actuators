from __future__ import annotations

import time

from dataclasses import dataclass
from enum import IntEnum
from typing import Annotated, Literal, Optional, Union

import can

from annotated_types import Interval, MaxLen


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


@dataclass
class GetDeviceIdRequest:
    communication_type: Literal[CommunicationType.GET_DEVICE_ID] = \
        CommunicationType.GET_DEVICE_ID


@dataclass
class GetDeviceIdResponse:
    id: bytes

    communication_type: Literal[CommunicationType.GET_DEVICE_ID] = \
        CommunicationType.GET_DEVICE_ID


type Request = Union[
    GetDeviceIdRequest
]


type Response = Union[
    GetDeviceIdResponse
]


type BytesLike = Union[bytes | bytearray]
type Data = Annotated[BytesLike, MaxLen(8)]
type DeviceId = Annotated[int, Interval(gt=0x00, le=0xff)]
type Extra = Annotated[int, Interval(ge=0x00, le=0xffff)]


def open(name: str = "can0", bitrate: int = 1000000) -> can.BusABC:
    return can.interface.Bus(
        interface="socketcan",
        channel=name,
        bitrate=bitrate
    )


def decode_get_id_response(data: Data, _: Extra) -> GetDeviceIdResponse:
    return GetDeviceIdResponse(bytes(data))


def decode(
    arbitration_id: int,
    data: Data
) -> tuple[DeviceId, DeviceId, Response]:
    print(arbitration_id)
    print(data)

    communication_type = (arbitration_id >> 24) & 0x1f
    extra = (arbitration_id >> 8) & 0xffff
    source_id = extra & 0xff
    destination_id = arbitration_id & 0xff

    match communication_type:
        case CommunicationType.GET_DEVICE_ID:
            response = decode_get_id_response(data, extra)
        case _:
            raise UnknownCommunicationTypeError(communication_type)

    return source_id, destination_id, response


def encode_get_device_id_request(_: GetDeviceIdRequest) -> tuple[int, bytes]:
    return 0, b"\x00" * 8


def encode(
    source_id: DeviceId,
    destination_id: DeviceId,
    request: Request
) -> tuple[int, bytes]:
    match request.communication_type:
        case CommunicationType.GET_DEVICE_ID:
            extra, data = encode_get_device_id_request(request)
        case _:
            raise NotImplementedError

    extra |= source_id

    arbitration_id = (
        (request.communication_type << 24) |
        (extra << 8) |
        (destination_id)
    )

    return arbitration_id, data


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
    timeout: Optional[float] = None
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
            # zero device ID. These frames are recognized as non-extended ID
            # frames.

            break

        if remaining is not None:
            remaining -= finish_time - start_time

    return decode(frame.arbitration_id, frame.data)


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
