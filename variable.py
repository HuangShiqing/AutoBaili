# from threading import Thread, Lock, Event
from multiprocessing import Lock, Event, Queue, Pipe  # shared_memory
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

    # pipe_gimg_send, pipe_gimg_recv = Pipe()
    # pipe_gshow_send, pipe_gshow_recv = Pipe()
    # pipe_gresult_send, pipe_gresult_recv = Pipe()
    # pipe_touch_send, pipe_touch_recv = Pipe()

    queue_gimg = Queue()
    queue_gshow = Queue()
    queue_gresult = Queue()
    queue_touch = Queue()