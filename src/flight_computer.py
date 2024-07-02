import math
import krpcConnection

conn = krpcConnection.get_conn()
vessel = krpcConnection.get_vessel()

orbit_reference_frame = vessel.orbit.body.reference_frame
flight = vessel.flight(orbit_reference_frame)

surface_altitude = conn.add_stream(getattr, flight, 'surface_altitude')
horizontal_speed = conn.add_stream(getattr, flight, 'horizontal_speed')
vertical_speed = conn.add_stream(getattr, flight, 'vertical_speed')
drag_vector = conn.add_stream(getattr, flight, 'drag')

gravity = conn.add_stream(getattr, vessel.orbit.body, 'surface_gravity')
available_thrust = conn.add_stream(getattr, vessel, 'available_thrust')
mass = conn.add_stream(getattr, vessel, 'mass')


def real_altitude():
    try:
        offset = 0
        for part in vessel.parts.all:
            pos_y = part.position(vessel.reference_frame)[1]
            if pos_y < offset:
                offset = pos_y
        return surface_altitude() - abs(offset)
    except Exception:
        return surface_altitude()


def terminal_velocity():
    if flight.terminal_velocity != 0:
        return flight.terminal_velocity
    else:
        return math.sqrt(vertical_speed() ** 2 + 2 * gravity() * real_altitude())


def acceleration_needed():
    return math.sqrt(acceleration_needed_horizontally() ** 2 + acceleration_needed_vertically() ** 2)


def acceleration_needed_vertically():
    if vertical_speed() >= 0:
        return 0
    return vertical_speed() ** 2 / (2 * real_altitude())


def acceleration_needed_horizontally():
    if burn_time_horizontally() == 0:
        return 0
    return horizontal_speed() / burn_time_horizontally()


def burn_time_needed():
    t = math.sqrt(burn_time_vertically() ** 2 +
                  burn_time_horizontally() ** 2)
    return round(t, 0)


def burn_time_vertically():
    t = abs(vertical_speed() / ((available_thrust()) / mass()))
    return round(t, 0)


def burn_time_horizontally():
    t = abs(horizontal_speed() / ((available_thrust()) / mass()))
    return round(t, 0)


def time_to_impact_vertically():
    t = abs(2 * real_altitude() / terminal_velocity())
    return round(t, 0)


def effective_acceleration():
    return (available_thrust() / mass()) - gravity()


def drag():
    d = math.sqrt(drag_vector()[0] ** 2 + drag_vector()[1] ** 2 + drag_vector()[2] ** 2)
    if math.isnan(d):
        return 0
    return d


def is_landed():
    return (vessel.situation == conn.space_center.VesselSituation.landed or
            vessel.situation == conn.space_center.VesselSituation.splashed or
            vessel.situation == conn.space_center.VesselSituation.pre_launch)


def set_vessel_to_retrograde():
    vessel.control.speed_mode = conn.space_center.SpeedMode.surface
    vessel.control.sas_mode = conn.space_center.SASMode.retrograde


def set_vessel_to_stability():
    vessel.control.speed_mode = conn.space_center.SpeedMode.surface
    vessel.control.sas_mode = conn.space_center.SASMode.stability_assist


def point_vessel_straight_up():
    vessel.control.sas = False
    vessel.auto_pilot.engage()
    vessel.auto_pilot.target_pitch_and_heading(90, 90)


def print_telemetry(ti, tb):
    print(f'')
    print(f'Acceleration needed: {acceleration_needed():.2f} m/s²')
    print(f'Impact in: {ti} s')
    print(f'Burn for: {tb} s')
    print(f'Burn in: T{t_signal(ti, tb)} {abs(ti - tb)} s')


def print_aero_breaking():
    print(f'')
    print(f'The {vessel.name} is aero breaking')


def t_signal(t1, t2):
    return '+' if t1 - t2 < 0 else '-'


def await_until_is_falling():
    vertical_speed_expression = conn.get_call(getattr, flight, 'vertical_speed')
    expr = conn.krpc.Expression.less_than(
        conn.krpc.Expression.call(vertical_speed_expression),
        conn.krpc.Expression.constant_double(0.0)
    )
    is_falling = conn.krpc.add_event(expr)
    with is_falling.condition:
        is_falling.wait()
    set_vessel_to_retrograde()
    print(f'The {vessel.name} is falling')


def await_until_below_altitude(altitude):
    altitude_expression = conn.get_call(getattr, flight, 'surface_altitude')
    expr = conn.krpc.Expression.less_than(
        conn.krpc.Expression.call(altitude_expression),
        conn.krpc.Expression.constant_double(altitude)
    )
    is_below_altitude = conn.krpc.add_event(expr)
    with is_below_altitude.condition:
        is_below_altitude.wait()
    print(f'The {vessel.name} is below {altitude} m')
