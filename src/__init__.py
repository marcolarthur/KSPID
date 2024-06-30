import math
import time

import hoverslam
import krpcConnection


# Function to calculate vertical position and velocity
def vertical_motion(v0v, h0, g, t):
    h = h0 + v0v * t - 0.5 * g * t ** 2
    vv = v0v - g * t
    return h, vv


# Function to calculate horizontal position and velocity
def horizontal_motion(v0h, t):
    x = v0h * t
    vh = v0h
    return x, vh


# Function to calculate thrust needed
def thrust(m, g, v0v, v0h, tf):
    Ft_v = m * (g + v0v / tf)
    Ft_h = m * (v0h / tf)
    return Ft_v, Ft_h


# Time to initiate the hoverslam burn (vertical)
tf_vertical = vertical_speed() / gravity()

# Time to initiate the hoverslam burn (horizontal)
tf_horizontal = 0 / v0h

# Choose the greater of the two times for safety
tf = max(tf_vertical, tf_horizontal)

# Calculate positions and velocities at tf
h, vv = vertical_motion(v0v, h0, g, tf)
x, vh = horizontal_motion(v0h, tf)

# Calculate the required thrust
Ft_v, Ft_h = thrust(m, g, v0v, v0h, tf)


def set_vessel_to_retrograde():
    vessel.control.sas = False
    vessel.control.rcs = False
    time.sleep(0.25)
    vessel.control.sas = True
    vessel.control.rcs = True
    time.sleep(0.25)
    vessel.control.speed_mode = conn.space_center.SpeedMode.surface
    vessel.control.sas_mode = conn.space_center.SASMode.retrograde


conn = krpcConnection.get_conn()
vessel = krpcConnection.get_vessel()

if vessel.situation == conn.space_center.VesselSituation.landed:
    print(f'{vessel.name} is already landed')
    exit()

orbit_reference_frame = vessel.orbit.body.reference_frame
flight = vessel.flight(orbit_reference_frame)
vertical_speed = conn.add_stream(getattr, flight, 'vertical_speed')
print('Vertical Speed = %.2f m/s' % vertical_speed())
horizontal_speed = conn.add_stream(getattr, flight, 'horizontal_speed')
print('Horizontal Speed = %.2f m/s' % horizontal_speed())

if vertical_speed() < 0.0:
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
    print(f'The {vessel.name} is falling')

set_vessel_to_retrograde()

surface_altitude = conn.add_stream(getattr, flight, 'surface_altitude')
gravity = conn.add_stream(getattr, vessel.orbit.body, 'surface_gravity')
atmosphere_density = conn.add_stream(getattr, flight, 'atmosphere_density')
drag_coefficient = conn.add_stream(getattr, flight, 'drag_coefficient')
available_thrust = conn.add_stream(getattr, vessel, 'available_thrust')
mass = conn.add_stream(getattr, vessel, 'mass')
drag_vector = conn.add_stream(getattr, flight, 'drag')
bounding_box = vessel.bounding_box(orbit_reference_frame)
rocket_height = bounding_box[1][1] - bounding_box[0][1]
cross_sectional_area = bounding_box[1][0] * bounding_box[1][2]

while True:
    terminal_velocity = calculate_terminal_velocity()
    acceleration_needed_to_stop = calculate_acceleration_needed()
    time_to_impact = calculate_time_to_impact()
    burn_time_needed = calculate_burn_time()

    print(f'')
    print(f'Terminal Velocity = {terminal_velocity:.2f} m/s')
    print(f'Acceleration needed = {acceleration_needed_to_stop:.2f} m/s^2')
    # print(f'Time to impact = {time_to_impact:.2f} s')
    # print(f'Burn time needed = {burn_time_needed:.2f} s')
    print(f'Burn in T- {time_to_impact - burn_time_needed:.0f} s')

    if burn_time_needed > time_to_impact:
        break
    time.sleep(1.1)

while vessel.situation != conn.space_center.VesselSituation.landed:
    if surface_altitude() < 500:
        vessel.control.gear = True

    if horizontal_speed() > 2.5:
        terminal_velocity = calculate_terminal_velocity()
    else:
        vessel.control.sas = False
        vessel.auto_pilot.engage()
        vessel.auto_pilot.target_pitch_and_heading(90, 90)
        terminal_velocity = vertical_speed()

    acceleration_effective = calculate_acceleration_effective()
    acceleration_needed = calculate_acceleration_needed()
    vessel.control.throttle = acceleration_needed / acceleration_effective
    print('Throttle = %.2f' % vessel.control.throttle)
    time.sleep(0.1)

vessel.control.throttle = 0
vessel.control.rcs = False
print(f'{vessel.name} is landed. Probably...')
