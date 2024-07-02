import time
import flight_computer as fc

CEILING_ALTITUDE = 10000

if fc.is_landed():
    print(f'{fc.vessel.name} is already landed')
    exit()

print('Vertical Speed: %.2f m/s' % fc.vertical_speed())
print('Horizontal Speed: %.2f m/s' % fc.horizontal_speed())
print('Surface Altitude: %.2f m' % fc.surface_altitude())

if fc.vertical_speed() < 0.0:
    fc.set_vessel_to_retrograde()
    print(f'{fc.vessel.name} is falling')
else:
    print(f'Waiting for the {fc.vessel.name} to start falling')
    fc.await_until_is_falling()

if fc.surface_altitude() > CEILING_ALTITUDE:
    print(f'Waiting for the {fc.vessel.name} to be below {CEILING_ALTITUDE} m')
    fc.await_until_below_altitude(CEILING_ALTITUDE)

while True:
    time_to_impact = fc.time_to_impact_vertically()
    burn_time_needed = fc.burn_time_needed()

    if fc.drag() > fc.available_thrust():
        fc.print_aero_breaking()
    else:
        fc.print_telemetry(time_to_impact, burn_time_needed)
        if burn_time_needed >= time_to_impact:
            break

    time.sleep(0.5)

count_1_sec = 0
while not fc.is_landed():
    if fc.horizontal_speed() > 2.5:
        acceleration_needed = fc.acceleration_needed()
    else:
        acceleration_needed = fc.acceleration_needed_vertically()
        fc.point_vessel_straight_up()
    fc.vessel.control.throttle = acceleration_needed / fc.effective_acceleration()

    if fc.real_altitude() < 500:
        fc.vessel.control.gear = True

    count_1_sec += 0.1
    if count_1_sec > 1:
        print('Throttle = %.2f' % fc.vessel.control.throttle)
        count_1_sec = 0.0

fc.vessel.control.throttle = 0
fc.vessel.control.rcs = False
print(f'{fc.vessel.name} is landed. Probably...')
