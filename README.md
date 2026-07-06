# actuators

Slick API for controlling various robotic actuators

## Example


```python
import math

from actuators import robstride


def main():
    bus = robstride.open()
    motor = robstride.PositionMotor(
        bus,
        0x03,
        robstride.PositionMotor.Calibration(
            kp=1.0,
            kd=0.1
        )
    )

    motor.disable()
    motor.set_zero()
    motor.move(2 * math.pi)


if __name__ == "__main__":
    main()
```
