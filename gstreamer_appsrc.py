from variable import GlobalVar

import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib

import numpy as np
from PIL import Image, ImageDraw, ImageFont

def cb_busmessage_state_change(bus, message, pipeline):
    if message.src == pipeline:
        oldstate, newstate, pending = message.parse_state_changed()
        old = Gst.Element.state_get_name(oldstate)
        new = Gst.Element.state_get_name(newstate)
        print("pipeline state changed from ", old, " to ", new)

# 显示
from fractions import Fraction

pts = 0
duration = 10 ** 9 / Fraction(30)


def draw_rect(draw, x1, y1, x2, y2):
    draw.line((x1, y1, x1, y2), 'red', 3)  # w1,h1,w2,h2
    draw.line((x2, y1, x2, y2), 'red', 3)  # w1,h1,w2,h2
    draw.line((x1, y1, x2, y1), 'red', 3)  # w1,h1,w2,h2
    draw.line((x1, y2, x2, y2), 'red', 3)  # w1,h1,w2,h2


def cb_appsrc(appsrc, b):
    # print("hi form cb_appsrc")
    global pts, duration

    # with GlobalVar.shared_array_gshow.get_lock():
    with GlobalVar.lock:
        # np_array = np.frombuffer(GlobalVar.shared_array_gshow.get_obj(), dtype="uint8").reshape(GlobalVar.array_shape)
        np_array = np.frombuffer(GlobalVar.shared_array_gshow, dtype="uint8").reshape(GlobalVar.array_shape)
        array = np_array.copy()

        np_array_result = np.frombuffer(GlobalVar.shared_array_result, dtype="float32").reshape([10, 7])
        result = np_array_result.copy()
    # result = GlobalVar.queue_gresult.get()
    # print(result)

    im = Image.fromarray(array)
    draw = ImageDraw.Draw(im)
    # print(result)
    draw_rect(draw, 915, 400, 956, 442)
    for r in result:
        draw_rect(draw, r[1], r[2], r[3], r[4])
    array = np.asarray(im)

    gst_buffer = Gst.Buffer.new_wrapped(array.tobytes())
    pts += duration
    gst_buffer.pts = pts
    gst_buffer.duration = duration
    ret = appsrc.emit("push-buffer", gst_buffer)

    # print("hi from cb_appsrc end")
    return Gst.FlowReturn.OK

def gst_appsrc_init():
    Gst.init([])

    pipeline2 = Gst.parse_launch(
        "appsrc is-live=True do-timestamp=True emit-signals=True block=True stream-type=0 format=GST_FORMAT_TIME caps=video/x-raw,format=RGB,width={},height={},framerate=30/1 ! videoconvert ! videoscale ! autovideosink ".format(
            GlobalVar.WIDTH, GlobalVar.HEIGHT))  # fpsdisplaysink text-overlay=false fps-update-interval=1000

    appsrc = pipeline2.get_by_name("appsrc0")
    appsrc.connect("need-data", cb_appsrc)
    bus2 = pipeline2.get_bus()
    bus2.add_signal_watch()
    bus2.connect("message::state-changed", cb_busmessage_state_change, pipeline2)

    return pipeline2