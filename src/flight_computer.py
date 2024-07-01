import math
import time
import krpcConnection

conn = krpcConnection.get_conn()
vessel = krpcConnection.get_vessel()
orbit_reference_frame = vessel.orbit.body.reference_frame
flight = vessel.flight(orbit_reference_frame)
surface_altitude = conn.add_stream(getattr, flight, 'surface_altitude')
gravity = conn.add_stream(getattr, vessel.orbit.body, 'surface_gravity')
atmosphere_density = conn.add_stream(getattr, flight, 'atmosphere_density')
drag_coefficient = conn.add_stream(getattr, flight, 'drag_coefficient')
available_thrust = conn.add_stream(getattr, vessel, 'available_thrust')
mass = conn.add_stream(getattr, vessel, 'mass')
center_of_mass_tuple = conn.add_stream(getattr, flight, 'center_of_mass')
drag_vector = conn.add_stream(getattr, flight, 'drag')


def real_altitude():
    offset = 0
    for part in vessel.parts.all:
        pos_y = part.position(vessel.reference_frame)[1]
        if pos_y < offset:
            offset = pos_y
    return surface_altitude() - abs(offset)


def cross_sectional_area():
    return bounding_box()[1][0] * bounding_box()[1][2]


def bounding_box():
    return vessel.bounding_box(orbit_reference_frame)


def terminal_velocity():
    if flight.terminal_velocity != 0:
        return flight.terminal_velocity

    if atmosphere_density() == 0 or drag_coefficient() == 0:
        return vertical_speed() + math.sqrt(2 * mass() * gravity())

    return vertical_speed() + math.sqrt(
        (2 * mass() * gravity()) / (atmosphere_density() * cross_sectional_area * drag_coefficient()))


def acceleration_needed():
    return (acceleration_needed_horizontally()
            + acceleration_needed_vertically())


def acceleration_needed_vertically():
    if vertical_speed() >= 0:
        return 0
    return vertical_speed() ** 2 / (2 * real_altitude())


def acceleration_needed_horizontally():
    return horizontal_speed() ** 2 / (2 * real_altitude())


def burn_time_needed():
    t = math.sqrt(burn_time_vertically() ** 2 +
                  burn_time_horizontally() ** 2)
    return round(t, 0)


def burn_time_vertically():
    t = abs(vertical_speed() / ((available_thrust() * 0.9) / mass()))
    return round(t, 0)


def burn_time_horizontally():
    t = abs(horizontal_speed() / ((available_thrust() * 0.9) / mass()))
    return round(t, 0)


def time_to_impact_vertically():
    t = (vertical_speed() + math.sqrt(vertical_speed() ** 2 + 2 * gravity() * real_altitude())) / gravity()
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


def reset_sas_rcs():
    vessel.control.sas = False
    vessel.control.rcs = False
    time.sleep(0.1)
    vessel.control.sas = True
    vessel.control.rcs = True
    time.sleep(0.1)


def set_vessel_to_retrograde():
    reset_sas_rcs()
    vessel.control.speed_mode = conn.space_center.SpeedMode.surface
    vessel.control.sas_mode = conn.space_center.SASMode.retrograde


def set_vessel_to_stability():
    reset_sas_rcs()
    vessel.control.speed_mode = conn.space_center.SpeedMode.surface
    vessel.control.sas_mode = conn.space_center.SASMode.stability_assist


def point_vessel_straight_up():
    vessel.control.sas = False
    vessel.auto_pilot.engage()
    vessel.auto_pilot.target_pitch_and_heading(90, 90)


def t_signal():
    return '+' if time_to_impact_vertically() - burn_time_needed() < 0 else '-'


if is_landed():
    print(f'{vessel.name} is already landed')
    exit()

vertical_speed = conn.add_stream(getattr, flight, 'vertical_speed')
print('Vertical Speed: %.2f m/s' % vertical_speed())
horizontal_speed = conn.add_stream(getattr, flight, 'horizontal_speed')
print('Horizontal Speed: %.2f m/s' % horizontal_speed())

if vertical_speed() < 0.0:
    set_vessel_to_retrograde()
    print(f'{vessel.name} is falling')
else:
    print(f'Waiting for the {vessel.name} to start falling')
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
