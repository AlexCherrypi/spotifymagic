import time
from datetime import datetime


def wait_until(execute_it_now):
    while True:
        diff = (execute_it_now - datetime.now()).total_seconds()
        if diff <= 0:
            return
        elif diff <= 0.1:
            time.sleep(0.001)
        elif diff <= 0.5:
            time.sleep(0.01)
        elif diff <= 1.5:
            time.sleep(0.1)
        else:
            time.sleep(1)
