import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst, GObject, GLib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import time,os

import torch
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import Dataset, DataLoader
from torchvision.models.resnet import resnet50
import torch.optim as optim
import torch.nn as nn

from threading import Thread,Lock,Event

from yolo import net
from minitouch import TouchStatus, MiniTouch, XY

WIDTH = 956
HEIGHT = 442


def cb_busmessage_state_change(bus,message,pipeline):
    if message.src == pipeline:
        oldstate,newstate,pending = message.parse_state_changed()
        old = Gst.Element.state_get_name(oldstate)
        new = Gst.Element.state_get_name(newstate)
        print("pipeline state changed from ",old," to ",new)


# 图像抓取
def cb_appsink(appsink):
    global gimg,lock,event
    #print("hi from cb_appsink")
    sample = appsink.emit("pull-sample")
    gst_buffer = sample.get_buffer()  # Gst.Buffer  
    array = np.ndarray(shape=(HEIGHT,WIDTH,3),buffer=gst_buffer.extract_dup(0,gst_buffer.get_size()),dtype='uint8')
    
    lock.acquire()
    gimg = array.copy()
    lock.release()
    
    event.set()
    #print("hi from cb_appsink end")
    return Gst.FlowReturn.OK

# 显示
from fractions import Fraction
pts = 0
duration = 10**9 / Fraction(30)
def draw_rect(draw, x1, y1, x2, y2):
    draw.line((x1, y1, x1, y2), 'red',3)#w1,h1,w2,h2
    draw.line((x2, y1, x2, y2), 'red',3)#w1,h1,w2,h2
    draw.line((x1, y1, x2, y1), 'red',3)#w1,h1,w2,h2
    draw.line((x1, y2, x2, y2), 'red',3)#w1,h1,w2,h2
def cb_appsrc(appsrc, b):
    #print("hi form cb_appsrc")
    global gshow,lock2, gresult
    global pts,duration

    lock2.acquire()
    array = gshow.copy()
    result = gresult.copy()
    lock2.release()

    im = Image.fromarray(array)
    draw = ImageDraw.Draw(im)
    # print(result)
    for r in result:
        draw_rect(draw, r[1], r[2], r[3], r[4])
    
    # if(result[0][-2]>0.8):
    #     draw.line((result[0][1], result[0][2], result[0][1], result[0][4]), 'red',3)#w1,h1,w2,h2
    #     draw.line((result[0][3], result[0][2], result[0][3], result[0][4]), 'red',3)#w1,h1,w2,h2
    #     draw.line((result[0][1], result[0][2], result[0][3], result[0][2]), 'red',3)#w1,h1,w2,h2
    #     draw.line((result[0][1], result[0][4], result[0][3], result[0][4]), 'red',3)#w1,h1,w2,h2
    array = np.asarray(im)

    gst_buffer = Gst.Buffer.new_wrapped(array.tobytes())
    pts += duration
    gst_buffer.pts = pts
    gst_buffer.duration = duration
    ret = appsrc.emit("push-buffer",gst_buffer)

    #print("hi from cb_appsrc end")
    return Gst.FlowReturn.OK

def gst_init():
    Gst.init([])
    
    pipeline = Gst.parse_launch("ximagesrc xname=mi9 ! videoconvert ! videoscale ! video/x-raw,format=RGB,width={},height={},framerate=30/1 ! appsink emit-signals=True".format(WIDTH,HEIGHT))
    pipeline2 = Gst.parse_launch("appsrc is-live=True do-timestamp=True emit-signals=True block=True stream-type=0 format=GST_FORMAT_TIME caps=video/x-raw,format=RGB,width={},height={},framerate=30/1 ! videoconvert ! videoscale ! autovideosink ".format(WIDTH,HEIGHT))    # fpsdisplaysink text-overlay=false fps-update-interval=1000
 
    appsink = pipeline.get_by_name("appsink0")
    appsink.connect("new-sample",cb_appsink)
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message::state-changed",cb_busmessage_state_change,pipeline)
    
    appsrc = pipeline2.get_by_name("appsrc0")
    appsrc.connect("need-data",cb_appsrc)
    bus2 = pipeline2.get_bus()
    bus2.add_signal_watch()
    bus2.connect("message::state-changed",cb_busmessage_state_change,pipeline2)

    return pipeline, pipeline2

class status:
    def __init__(self):
        self.prediction = []
        self._net = net(cfg_path="./cfg/yolov3-tiny.cfg", weights_path="./backup/yolov3-tiny_60000.weights", num_classes=1)
        
    def get_status(self, img_np):
        prediction = self._net.inference(img_np)
        return prediction

def detect_init():
    def detect():
        global event, lock, gimg, lock2, gshow, gresult
        s = status()
        while(1):
            event.wait()
                    
            lock.acquire()
            array = gimg.copy()
            lock.release()
            
            # t1 = time.time()
            result = s.get_status(array)
            # t2 = time.time()
            # print("time: ", t2-t1) #yolov3_tiny: 0.02s

            lock2.acquire()
            gshow = array.copy()
            # if result[0][-2]>0.5 :
            #     gresult = result.copy()
            gresult = result.copy()
            lock2.release()

            # event.clear()
    t = Thread(target=detect, name='detect')
    t.start()

import math
def action_init():
    
    def action():
        global lock2, gresult, event_down, event_up
        
        minitouch = MiniTouch()
        contact_id = 4
        while True:
            
            if event_down.is_set():
                event_down.clear()
                print("get the event_down")
                minitouch.slice_line(contact_id, XY(335, 1825), XY(330, 1960), 2000, down=True, up=False)                
            # elif event_up.is_set():
            #     print("get the event_up")
                time.sleep(1.8)

                lock2.acquire()
                result = gresult.copy()
                lock2.release()
                
                # get angle
                x_detect = (result[0][1]+result[0][3])/2
                y_detect = (result[0][2]+result[0][4])/2

                delta_x = HEIGHT - y_detect - HEIGHT/2
                # sub = (20-0.0905*delta_x)
                sub = 0.41*delta_x-33.2
                delta_x += sub
                delta_y = x_detect  - WIDTH/2

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

                angle = math.atan(delta_x/delta_y)*180/math.pi

                # 4 quadrant
                if delta_x >=0 and delta_y>=0:#右上角
                    pass
                elif delta_x >0 and delta_y<0:#左上角
                    angle = 180+angle
                elif delta_x <0 and delta_y<0:#左下角
                    angle = 180+angle
                elif delta_x <0 and delta_y>0:#右下角
                    pass

                print("result: ", result)
                print("delta_x ", delta_x)
                print("sub ", sub)
                print("delta_y ", delta_y)
                print("angle: ", angle)

                # angle = 180
                minitouch.slice_circular(contact_id, XY(335, 1825), XY(335, 1960), angle, 1000, down=False, up=True)
                event_up.clear()
            
    t = Thread(target=action, name='action')
    t.start()

def touch_status_init(event_down, event_up):
    
    def action(event_down, event_up):
        touch_status = TouchStatus("/dev/input/event4", event_down, event_up)
        touch_status.process()

    t = Thread(target=action, args=(event_down, event_up), name='touch_status')
    t.start()

if __name__ == "__main__":
    # global define
    gimg = np.zeros((HEIGHT,WIDTH,3),dtype='uint8')
    gshow = np.zeros((HEIGHT,WIDTH,3),dtype='uint8')
    gresult = [[0, 100, 100, 100,100, 0, 1.0, 0]]
    lock = Lock()
    lock2 = Lock()
    event = Event()
    # event2 = Event()
    event_down = Event()
    event_up = Event()

    touch_status_init(event_down, event_up)
    action_init()
    detect_init()
    pipeline, pipeline2 = gst_init()
    ret = pipeline.set_state(Gst.State.PLAYING)
    ret = pipeline2.set_state(Gst.State.PLAYING)
    GLib.MainLoop().run()
