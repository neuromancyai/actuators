# actuators

Slick API for controlling various robotic actuators

## Example


```python
import math
import time

from actuators import robstride


def main():
    calibration = robstride.PositionMotor.Calibration(
        gear=1.0,
        kp=1.0,
        kd=0.1
    )

    with robstride.open() as bus:
        with robstride.PositionMotor(bus, 0x03, calibration) as motor:
            motor.set_zero()
            motor.move(2 * math.pi)

            time.sleep(1.0)


if __name__ == "__main__":
    main()
```

## Installation

The best way to install this library is using the `uv` package manager:

```
uv add git+https://github.com/neuromancyai/actuators
```
