# def calculate_time_to_impact(_surface_altitude, _gravity, _velocity):
#     return (_velocity + math.sqrt(_velocity ** 2 + 2 * _gravity * _surface_altitude)) / _gravity
#
#
# def calculate_burn_duration_time(_speed, _gravity, _available_thrust, _mass, _drag):
#     drag = math.sqrt(_drag[0] ** 2 + _drag[1] ** 2 + _drag[2] ** 2)
#     if not math.isnan(drag):
#         return (_speed / _gravity) * (_mass / (_available_thrust - drag))
#     else:
#         return (_speed / _gravity) * (_mass / _available_thrust)

while True:
    time_to_impact = calculate_time_to_impact((surface_altitude() - rocket_height), gravity(), vertical_speed())
    time_to_burn = calculate_burn_duration_time(velocity, gravity(),
                                                available_thrust(), mass(),
                                                drag_vector())

    if 10 > time_to_impact - time_to_burn > 0 and count_1_second >= 1:
        print(f'BURN IN T-{time_to_impact - time_to_burn:.0f} s')
        print(f'')
        count_1_second = 0

    if time_to_burn > time_to_impact:
        break
    count_1_second += 0.1
    time.sleep(0.1)

max_deceleration = vertical_speed() ** 2 / (2 * (surface_altitude() - rocket_height) * gravity())
vessel.control.throttle = 1



while True:
    print('Horizontal Speed = %.2f m/s' % horizontal_speed())
    if -2.5 > horizontal_speed() < 2.5:
        vessel.control.sas = False
        vessel.auto_pilot.engage()
        vessel.auto_pilot.target_pitch_and_heading(90, 90)

    if vessel.situation == conn.space_center.VesselSituation.landed:
        vessel.control.throttle = 0
        print('Landed. Probably')
        break

    deceleration = vertical_speed() ** 2 / (2 * (surface_altitude() - rocket_height) * gravity())

    if deceleration <= gravity() * 2 and surface_altitude() < 500:
        vessel.control.gear = True

    if vertical_speed() >= 0:
        vessel.control.throttle = 0
    else:
        vessel.control.throttle = deceleration / max_deceleration

    if count_1_second >= 1:
        print(f'Vertical Speed = {vertical_speed():.2f}')
        print(f'Deceleration = {deceleration:.2f}')
        print(f'Throttle = {vessel.control.throttle:.2f}')
        print(f'')
        count_1_second = 0
    count_1_second += 0.1
    time.sleep(0.1)


 print(
     f'Time until impact = {calculate_time_to_impact((surface_altitude() - rocket_height), gravity(), vertical_speed()):.2f} s')