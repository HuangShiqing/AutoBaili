from variable import GlobalVar
from multiprocessing import Process, Lock, Event, Queue
import time, math
from pyminitouch import safe_connection, safe_device, MNTDevice, CommandBuilder


class XY(object):
    def __init__(self, x, y):
        self._x = (int)(x)
        self._y = (int)(y)

    def get_x(self):
        return self._x

    def get_y(self):
        return self._y

    def set_x(self, x):
        self._x = x

    def set_y(self, y):
        self._y = y


class MiniTouch(object):
    def __init__(self):
        self.device = MNTDevice(GlobalVar.DEVICE_ID)

    def __del__(self):  # 当程序结束时运行
        self.device.stop()
        # print("析构函数")

    def tap(self, contact_id, xy, time_consume, down=True, up=True):
        pressure = 50
        # with safe_connection(DEVICE_ID) as connection:
        builder = CommandBuilder()
        if down:
            builder.down(contact_id, xy.get_x(), xy.get_y(), pressure)
            builder.commit()
            builder.publish(self.device.connection)

        builder.wait(time_consume)
        builder.commit()
        builder.publish(self.device.connection)

        if up:
            builder.up(contact_id)
            builder.commit()
            builder.publish(self.device.connection)

    def slice_line(self, contact_id, xy_begin, xy_end, time_consume, down=True, up=True):
        pressure = 50
        num_points = 2  # 包含落点和抬起点总共的点数, num_points>=2
        delta_x = xy_end.get_x() - xy_begin.get_x()
        delta_y = xy_end.get_y() - xy_begin.get_y()
        interval_x = delta_x / (num_points - 1)
        interval_y = delta_y / (num_points - 1)
        xy_list = [XY(xy_begin.get_x() + i * interval_x, xy_begin.get_y() + i * interval_y) for i in range(num_points)]
        interval_time = (int)(time_consume / (num_points - 1))
        # for xy_ in xy_list:
        #     print(xy_.get_y(), xy_.get_x())
        # print(interval_time)    

        # with safe_connection(DEVICE_ID) as connection:
        builder = CommandBuilder()
        if down:
            builder.down(contact_id, xy_list[0].get_x(), xy_list[0].get_y(), pressure)
            builder.commit()
            builder.publish(self.device.connection)
        for i in range(1, num_points):
            # builder.wait(interval_time)
            builder.commit()
            builder.move(contact_id, xy_list[i].get_x(), xy_list[i].get_y(), pressure)
            builder.commit()
            builder.publish(self.device.connection)

        if up:
            builder.up(contact_id)
            builder.commit()
            builder.publish(self.device.connection)

    def slice_circular(self, contact_id, xy_center, xy_begin, angle, time_consume, down=True, up=True):
        pressure = 50
        num_points = 2  # 包含落点和抬起点总共的点数, num_points>=2
        interval_theta = angle / (num_points - 1)
        xy_list = []
        interval_time = (int)(time_consume / (num_points - 1))
        # for i in range(num_points):
        #     print(i*interval_theta, math.sin(i*interval_theta*math.pi/180))

        for i in range(num_points):
            y = xy_center.get_y() + (xy_begin.get_y() - xy_center.get_y()) * math.cos(
                i * interval_theta * math.pi / 180) - (xy_begin.get_x() - xy_center.get_x()) * math.sin(
                i * interval_theta * math.pi / 180)
            x = xy_center.get_x() + (xy_begin.get_x() - xy_center.get_x()) * math.cos(
                i * interval_theta * math.pi / 180) + (xy_begin.get_y() - xy_center.get_y()) * math.sin(
                i * interval_theta * math.pi / 180)
            # r = xy_begin.get_y()-xy_center.get_y()
            # y = xy_center.get_y()+r*math.cos(i*interval_theta*math.pi/180)
            # x = xy_center.get_x()+r*math.sin(i*interval_theta*math.pi/180)
            xy_list.append(XY(x, y))

        # with safe_connection(DEVICE_ID) as connection:
        builder = CommandBuilder()
        if down == True:
            builder.down(contact_id, xy_list[0].get_x(), xy_list[0].get_y(), pressure)
            builder.commit()
            builder.publish(self.device.connection)

        for i in range(1, num_points):
            # builder.wait(interval_time)
            builder.commit()
            builder.move(contact_id, xy_list[i].get_x(), xy_list[i].get_y(), pressure)
            builder.commit()
            builder.publish(self.device.connection)

        # builder.wait(time_consume)#temp
        if up == True:
            builder.up(contact_id)
            builder.commit()
            builder.publish(self.device.connection)


import signal
import subprocess
import re


class TouchStatus(object):
    def __init__(self, device, event_down):
        self._device = device
        self._act = -1  # -1:无 0:按下 1：抬起
        self._act_touch_index = 0
        self._interested_index = -1
        self._xy = XY(0, 0)
        self._count = 0
        self._event_down = event_down

    def listening(self):
        # cmd = r'adb exec-out getevent -l /dev/input/event4'
        cmd = r'adb exec-out getevent -l ' + self._device
        try:
            p1 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            pattern_slot = re.compile(r'0000000\d')
            pattern_position = re.compile(r'00000\w+')
            line_group = []
            print("starting listening the touch situation")
            for line in p1.stdout:
                line = line.decode(encoding="utf-8", errors="ignore")
                if 'SYN_REPORT' in line:
                    # init
                    self._act = -1
                    for subline in line_group:
                        if "ABS_MT_TRACKING_ID" in subline:
                            if "ffffffff" in subline:  # and len(line_group) in [1,2, 3, 4]:
                                self._act = 1  # 抬起
                                self._count -= 1
                            else:  # elif len(line_group) in [4, 5, 6]:
                                self._act = 0  # 按下
                                self._count += 1
                        elif "ABS_MT_SLOT" in subline:
                            a = pattern_slot.findall(subline)[0]
                            self._act_touch_index = int(a)
                        elif "ABS_MT_POSITION_X" in subline:
                            b = pattern_position.findall(subline)[0]
                            self._xy.set_x(int(b, 16))
                        elif "ABS_MT_POSITION_Y" in subline:
                            b = pattern_position.findall(subline)[0]
                            self._xy.set_y(int(b, 16))

                            # print(line_group)
                    line_group.clear()
                    # TODO:
                    if self._act == 0:  # 按下
                        if self._xy.get_x() < 100 and self._xy.get_y() > 2200:
                            self._interested_index = self._act_touch_index
                            # self._event_down.send(["down"])
                            self._event_down.put(["down"])
                            # print("act_: down")
                            # print("act_touch_index_: ", self._act_touch_index)
                            # print("x: ", self._xy.get_x())
                            # print("y: ", self._xy.get_y())
                            # print("")

                    elif self._act == 1:  # 抬起
                        if self._interested_index == self._act_touch_index:
                            self._interested_index = -1
                            # self.event_up_.set()                           
                        # print("act_: up")
                        # print("act_touch_index_: ", self._act_touch_index)
                        # print("")
                else:
                    line_group.append(line)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    def touch_status_thread(event_down):
        touch_status = TouchStatus(GlobalVar.DEV_INPUT, event_down)
        touch_status.listening()


    def touch_action_thread():
        minitouch = MiniTouch()
        contact_id = 4
        while True:
            # recv = GlobalVar.pipe_touch_recv.recv()
            recv = GlobalVar.queue_touch.get()
            if recv[0] == 'down':
                print("get the event_down")
                minitouch.slice_line(contact_id, XY(335, 1825), XY(330, 1960), 0, down=True, up=True)


    Process(target=touch_status_thread, args=(GlobalVar.queue_touch,),
            name='touch_status_thread').start()
    Process(target=touch_action_thread, name='touch_action_thread').start()
    while True:
        pass