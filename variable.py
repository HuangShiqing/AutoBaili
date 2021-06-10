# from threading import Thread, Lock, Event
from multiprocessing import Lock, Event, Queue, Pipe, Array, shared_memory
import ctypes
import numpy as np


class GlobalVar(object):
    print("hi from GlobalVar")
    WIDTH = 956
    HEIGHT = 442

    DEVICE_ID = "c759970d"
    DEV_INPUT = "/dev/input/event4"

    CFG_PATH = "./cfg/yolov3-tiny.cfg"
    WEIGHT_PATH = "./backup/yolov3-tiny_60000.weights"
    LABEL = ["enemy"]

    queue_touch = Queue()

    array_shape = (HEIGHT, WIDTH, 3)
    shared_array_gimg = Array(ctypes.c_uint8, int(WIDTH * HEIGHT * 3))

    shared_array_gshow = Array(ctypes.c_uint8, int(WIDTH * HEIGHT * 3), lock=False)
    shared_array_result = Array(ctypes.c_float, int(10*7), lock=False)
    lock = Lock()


if __name__ == '__main__':
    a = GlobalVar()
    exit()
