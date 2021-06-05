from variable import GlobalVar

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib

import numpy as np

def cb_busmessage_state_change(bus, message, pipeline):
    if message.src == pipeline:
        oldstate, newstate, pending = message.parse_state_changed()
        old = Gst.Element.state_get_name(oldstate)
        new = Gst.Element.state_get_name(newstate)
        print("pipeline state changed from ", old, " to ", new)

# 图像抓取
def cb_appsink(appsink):
    # print("hi from cb_appsink")
    sample = appsink.emit("pull-sample")
    gst_buffer = sample.get_buffer()  # Gst.Buffer
    array = np.ndarray(shape=(GlobalVar.HEIGHT, GlobalVar.WIDTH, 3),
                       buffer=gst_buffer.extract_dup(0, gst_buffer.get_size()), dtype='uint8')

    # GlobalVar.pipe_gimg_send.send(array)
    GlobalVar.queue_gimg.put(array)

    # print("hi from cb_appsink end")
    return Gst.FlowReturn.OK

def gst_appsink_init():
    Gst.init([])

    pipeline = Gst.parse_launch(
        "ximagesrc xname=mi9 ! videoconvert ! videoscale ! video/x-raw,format=RGB,width={},height={},framerate=30/1 ! appsink emit-signals=True".format(
            GlobalVar.WIDTH, GlobalVar.HEIGHT))

    appsink = pipeline.get_by_name("appsink0")
    appsink.connect("new-sample", cb_appsink)
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message::state-changed", cb_busmessage_state_change, pipeline)

    return pipeline