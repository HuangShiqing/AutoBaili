from variable import GlobalVar
# from gstreamer import *
from gstreamer_appsink import gst_appsink_init
from gstreamer_appsrc import gst_appsrc_init
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib

from yolo import YoloNet
from minitouch import TouchStatus, MiniTouch, XY

import time
import math

from multiprocessing import Process


def detect_thread(CFG_PATH, WEIGHT_PATH, LABEL):
    yolo_net = YoloNet(CFG_PATH, WEIGHT_PATH, LABEL)

    # t1 = time.time()
    while True:
        # array = GlobalVar.pipe_gimg_recv.recv()
        array = GlobalVar.queue_gimg.get()

        # t1 = time.time()
        inp_data, orig_ims = yolo_net.prepare(array)
        prediction_tmp = yolo_net.inference(inp_data)
        result = yolo_net.deprepare(prediction_tmp)
        # result = [[0, 100, 100, 100, 100, 0, 1.0, 0]]
        # t2 = time.time()
        # print("time: ", t2-t1) #yolov3_tiny: 0.02s

        # t1 = time.time()-t1
        # print(t1)

        # GlobalVar.pipe_gshow_send.send(array)
        # GlobalVar.pipe_gresult_send.send(result)
        GlobalVar.queue_gshow.put(array)
        GlobalVar.queue_gresult.put(result)


def calculate_angle(result):
    # get angle
    # TODO:
    x_detect = (result[0][1] + result[0][3]) / 2
    y_detect = (result[0][2] + result[0][4]) / 2

    delta_x = GlobalVar.HEIGHT - y_detect - GlobalVar.HEIGHT / 2
    # magic
    sub = 0.41 * delta_x - 33.2
    delta_x += sub
    delta_y = x_detect - GlobalVar.WIDTH / 2

    # transform
    # x1=745, y1=305
    # y2=x1/956*2339, x2=(442-y1)/442*1079
    # y2=1882, x2=335

    #  detect___x=956________
    # |y=442
    # |
    # |
    # |
    # |x=1079
    # |_________y=2339________
    # minitouch

    angle = math.atan(delta_x / delta_y) * 180 / math.pi

    # 4 quadrant
    if delta_x >= 0 and delta_y >= 0:  # 右上角
        pass
    elif delta_x > 0 and delta_y < 0:  # 左上角
        angle = 180 + angle
    elif delta_x < 0 and delta_y < 0:  # 左下角
        angle = 180 + angle
    elif delta_x < 0 and delta_y > 0:  # 右下角
        pass

    return angle


def touch_action_thread():
    minitouch = MiniTouch()
    contact_id = 4
    while True:
        # recv = GlobalVar.pipe_touch_recv.recv()
        recv = GlobalVar.queue_touch.get()
        if recv[0] == 'down':
            print("get the event_down")
            minitouch.slice_line(contact_id, XY(335, 1825), XY(330, 1960), 2000, down=True, up=False)

            time.sleep(1.8)

            # result = GlobalVar.pipe_gresult_recv.recv()
            result = GlobalVar.queue_gresult.get()

            angle = calculate_angle(result)

            print("result: ", result)
            # print("delta_x ", delta_x)
            # print("sub ", sub)
            # print("delta_y ", delta_y)
            # print("angle: ", angle)

            # angle = 180
            minitouch.slice_circular(contact_id, XY(335, 1825), XY(335, 1960), angle, 1000, down=False, up=True)


def touch_status_thread(event_down):
    touch_status = TouchStatus(GlobalVar.DEV_INPUT, event_down)
    touch_status.listening()

def gstreamer_appsink_thread():
    pipeline = gst_appsink_init()
    ret = pipeline.set_state(Gst.State.PLAYING)
    GLib.MainLoop().run()

def gstreamer_appsrc_thread():
    pipeline = gst_appsrc_init()
    ret = pipeline.set_state(Gst.State.PLAYING)
    GLib.MainLoop().run()


if __name__ == "__main__":
    Process(target=touch_status_thread, args=(GlobalVar.queue_touch,),
                            name='touch_status_thread').start()
    Process(target=touch_action_thread, name='touch_action_thread').start()
    Process(target=detect_thread, args=(GlobalVar.CFG_PATH, GlobalVar.WEIGHT_PATH, GlobalVar.LABEL),
                            name='detect_thread').start()
    Process(target=gstreamer_appsrc_thread, name='gstreamer_appsrc_thread').start()
    gstreamer_appsink_thread()
