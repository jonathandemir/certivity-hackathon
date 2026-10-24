# spec: Pedal Misapplication Assist (ACPE)

Synthetic test specification written by the team for the overfitting check (X-R175): it lets the main-goal pipeline run
on UN R175 with Certivity's `subgoal/dev/requirements_old.json` as a second reference list. Written from general product
knowledge, not from the regulation text or the reference list.

## Product Type

Acceleration control for pedal error: a driver-assistance function of a passenger car that suppresses unintended
acceleration when the driver presses the accelerator instead of the brake pedal while an obstacle is close to the
vehicle, for example when parking.

## Vehicle Category

M1 — passenger car with automatic transmission.

## Function

- Detects obstacles in front of and behind the vehicle at low speed or standstill
- Detects a sudden, strong accelerator pedal application that is likely a pedal error
- Limits the drive torque so that a collision with the obstacle is prevented or mitigated
- Informs the driver when it intervenes and when the function is not available or deactivated
- Can be deactivated by the driver via a switch in the vehicle settings

## Main Parts

- Ultrasonic parking sensors in the front and rear bumper (4 + 4)
- Front camera module
- Control unit (software function in the parking-assistance ECU)
- Interface to the accelerator pedal position sensor and to the powertrain control unit (torque request)
- Driver information via instrument cluster messages and acoustic signal
- Deactivation switch in the infotainment settings menu

## Technology

Electronic control unit with sensor fusion of ultrasonic sensors and camera; communication over the vehicle CAN bus;
12 V supply.
