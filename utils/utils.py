
import time


def get_mins_in_timestamp():
    now = time.time()
    minutes_ago = now - (4 * 60)
    return int(minutes_ago * 1000000)
