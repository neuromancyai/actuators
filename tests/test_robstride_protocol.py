import pytest

from actuators.driver.robstride.protocol import (
    ControlRequest,
    DisableRequest,
    DeviceId,
    EnableRequest,
    GetDeviceIdRequest,
    GetDeviceIdResponse,
    Request,
    Response,
    SetZeroPositionRequest,
    StatusResponse,
    decode,
    encode
)


@pytest.mark.parametrize(
    "input, output",
    [
        (
            (0xff, 0x14, GetDeviceIdRequest()),
            (0xff14, b"\x00" * 8)
        ),
        (
            (
                0xff,
                0x14,
                ControlRequest(
                    position=2.4,
                    kp=20.0,
                    kd=0.5,
                    velocity=1.0,
                    torque=16.0
                )
            ),
            (0x1f87614, b"\x98q\x82\xe7\n=\x19\x99")
        ),
        (
            (0xff, 0x14, EnableRequest()),
            (0x0300ff14, b"\x00" * 8)
        ),
        (
            (0xff, 0x14, DisableRequest()),
            (0x0400ff14, b"\x00" * 8)
        ),
        (
            (0xff, 0x14, SetZeroPositionRequest()),
            (0x0600ff14, b'\x01\x00\x00\x00\x00\x00\x00\x00')
        )
    ]
)
def test_encoder(
    input: tuple[DeviceId, DeviceId, Request],
    output: tuple[int, bytes]
) -> None:
    assert encode(*input) == output


@pytest.mark.parametrize(
    "input, output",
    [
        (
            (0x3fe, b"\x14A0 \x9c#7\r"),
            (0x03, 0xfe, GetDeviceIdResponse(id=b"\x14A0 \x9c#7\r"))
        ),
        (
            (0x20003ff, b"o\x9c\x7f\x94\x7f\xff\x016"),
            (
                0x03,
                0xff,
                StatusResponse(
                    mode=0,
                    uncalibrated=False,
                    stall=False,
                    magnetic_encoder_fault=False,
                    overtemperature=False,
                    overcurrent=False,
                    undervoltage=False,
                    position=-1.6088114483241291,
                    velocity=-0.14368114261299558,
                    torque=0.0,
                    temperature=31.0
                )
            )
        ),
        (
            (0x20003ff, b"\x7f\xff\x7f\xf8\x7f\xff\x01@"),
            (
                0x03,
                0xff,
                StatusResponse(
                    mode=0,
                    uncalibrated=False,
                    stall=False,
                    magnetic_encoder_fault=False,
                    overtemperature=False,
                    overcurrent=False,
                    undervoltage=False,
                    position=0.0,
                    velocity=-0.009399700918606868,
                    torque=0.0,
                    temperature=32.0
                )
            )
        ),
        (
            (0x28003ff, b":M\x83:\x80M\x01J"),
            (
                0x03,
                0xff,
                StatusResponse(
                    mode=2,
                    uncalibrated=False,
                    stall=False,
                    magnetic_encoder_fault=False,
                    overtemperature=False,
                    overcurrent=False,
                    undervoltage=False,
                    position=-6.8425301218114685,
                    velocity=1.1105075228125836,
                    torque=0.04046754356517113,
                    temperature=33.0,
                )
            )       
        )
    ]
)
def test_decoder(
    input: tuple[int, bytes],
    output: tuple[DeviceId, DeviceId, Response]
) -> None:
    assert decode(*input) == output
