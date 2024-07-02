import time
import flight_computer as fc

time_to_impact = fc.time_to_impact_vertically()
burn_time_needed = fc.burn_time_needed()
fc.print_telemetry(time_to_impact, burn_time_needed)

while True:
    time_to_impact = fc.time_to_impact_vertically()
    burn_time_needed = fc.burn_time_needed()

    if fc.available_thrust() > fc.drag():
        fc.print_telemetry(time_to_impact, burn_time_needed)
        if burn_time_needed >= time_to_impact:
            break
    elif burn_time_needed >= time_to_impact:
        fc.print_aero_breaking(time_to_impact, burn_time_needed)

    time.sleep(1)

count_1_sec = 0
while not fc.is_landed():
    if fc.real_altitude() < 500:
        fc.vessel.control.gear = True

    if fc.horizontal_speed() > 2.5:
        acceleration_needed = fc.acceleration_needed()
    else:
        acceleration_needed = fc.acceleration_needed_vertically()
        fc.point_vessel_straight_up()

    fc.vessel.control.throttle = acceleration_needed / fc.effective_acceleration()

    count_1_sec += 0.1
    if count_1_sec > 1:
        print('Throttle = %.2f' % fc.vessel.control.throttle)
        count_1_sec = 0.0

    time.sleep(0.1)

fc.vessel.control.throttle = 0
fc.vessel.control.rcs = False
print(f'{fc.vessel.name} is landed. Probably...')
