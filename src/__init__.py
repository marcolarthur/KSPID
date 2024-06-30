import time
import flight_computer as fc

while True:
    time_to_impact = fc.time_to_impact_vertically()
    burn_time_needed = fc.burn_time_needed()

    print(f'')
    print(f'Acceleration needed: {fc.acceleration_needed():.2f} m/s²')
    print(f'Impact in: {time_to_impact} s')
    print(f'Burn for: {burn_time_needed} s')
    print(f'Burn in: T{fc.t_signal()} {abs(time_to_impact - burn_time_needed)} s')

    if fc.available_thrust() > fc.drag() and fc.real_altitude() < 10000:
        if burn_time_needed >= time_to_impact:
            break
    elif burn_time_needed >= time_to_impact:
        print('but the drag is slowing the vessel enough to not burn yet')

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
print(fc.real_altitude())
print(f'{fc.vessel.name} is landed. Probably...')
