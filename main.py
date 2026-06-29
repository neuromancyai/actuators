import math

import actuators.driver.robstride.protocol
import actuators.driver.robstride.motor


def main():
    bus = actuators.driver.robstride.protocol.open()
    motor = actuators.driver.robstride.motor.PositionMotor(
        bus,
        0x03,
        actuators.driver.robstride.motor.PositionMotor.Calibration(
            kp=1.0,
            kd=0.1
        )
    )

    motor.disable()
    motor.zero()
    motor.move(2 * math.pi)


if __name__ == "__main__":
    main()
