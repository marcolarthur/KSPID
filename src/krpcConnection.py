import time
import krpc


def connect_to_krpc():
    while True:
        try:
            _conn = krpc.connect(
                name='PID_KSP',
                address='127.0.0.1',
                rpc_port=50000, stream_port=50001)
            print('Connected. Starting the script...')
            return _conn
        except ConnectionRefusedError as e:
            print(f'Connection failed: {e}. Retrying in 10 seconds...')
            time.sleep(10)


conn = connect_to_krpc()

vessel = conn.space_center.active_vessel
vessel.control.sas = False
vessel.control.rcs = False
time.sleep(0.1)
vessel.control.sas = True
vessel.control.rcs = True
time.sleep(1)


def get_conn():
    return conn


def get_vessel():
    return vessel
