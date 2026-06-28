import pytest

from actuators.rs02 import (
    DeviceId,
    GetDeviceIdRequest,
    GetDeviceIdResponse,
    Request,
    Response,
    encode,
    decode
)


@pytest.mark.parametrize(
    "input, output",
    [
        (
            (0xff, 0x14, GetDeviceIdRequest()),
            (0xff14, b"\x00" * 8)
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
                (3, 254, GetDeviceIdResponse(id=b"\x14A0 \x9c#7\r"))
            )
        ]
)
def test_decoder(
    input: tuple[int, bytes],
    output: tuple[DeviceId, DeviceId, Response]
) -> None:
    assert decode(*input) == output
