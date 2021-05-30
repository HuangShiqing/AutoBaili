import time
import math
from pyminitouch import safe_connection, safe_device, MNTDevice, CommandBuilder
_DEVICE_ID = 'c759970d'

class XY(object):
    def __init__(self, x, y):
        self._x = (int)(x)        
        self._y = (int)(y)
    def x(self):
        return self._x
    def y(self):
        return self._y


class MiniTouch(object):
    def __init__(self):
        self.device = MNTDevice(_DEVICE_ID)

    def __del__(self):#当程序结束时运行
        self.device.stop()
        # print("析构函数")

    def tap(self, contact_id, xy, time_consume, down=True, up=True):
        pressure = 50
        # with safe_connection(_DEVICE_ID) as connection:
        builder = CommandBuilder()
        if down:
            builder.down(contact_id, xy.x(), xy.y(), pressure)
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
        num_points = 2 #包含落点和抬起点总共的点数, num_points>=2
        delta_x = xy_end.x() - xy_begin.x()
        delta_y = xy_end.y() - xy_begin.y()
        interval_x = delta_x / (num_points-1)
        interval_y = delta_y / (num_points-1)
        xy_list = [XY(xy_begin.x() + i * interval_x, xy_begin.y() + i * interval_y) for i in range(num_points)]
        interval_time = (int)(time_consume / (num_points-1))
        # for xy_ in xy_list:
        #     print(xy_.y(), xy_.x())
        # print(interval_time)    

        # with safe_connection(_DEVICE_ID) as connection:
        builder = CommandBuilder()
        if down:
            builder.down(contact_id, xy_list[0].x(), xy_list[0].y(), pressure)
            builder.commit()
            builder.publish(self.device.connection)
        for i in range(1, num_points):
            # builder.wait(interval_time)
            builder.commit()
            builder.move(contact_id, xy_list[i].x(), xy_list[i].y(), pressure)
            builder.commit()
            builder.publish(self.device.connection)

        if up:
            builder.up(contact_id)
            builder.commit()
            builder.publish(self.device.connection)

    def slice_circular(self, contact_id, xy_center, xy_begin, angle, time_consume, down=True, up=True):
        pressure = 50
        num_points = 2 #包含落点和抬起点总共的点数, num_points>=2
        interval_theta = angle/(num_points-1)
        xy_list = []
        interval_time = (int)(time_consume / (num_points-1))
        # for i in range(num_points):
        #     print(i*interval_theta, math.sin(i*interval_theta*math.pi/180))
           
        for i in range(num_points):
            y = xy_center.y()+(xy_begin.y()-xy_center.y())*math.cos(i*interval_theta*math.pi/180)-(xy_begin.x()-xy_center.x())*math.sin(i*interval_theta*math.pi/180)
            x = xy_center.x()+(xy_begin.x()-xy_center.x())*math.cos(i*interval_theta*math.pi/180)+(xy_begin.y()-xy_center.y())*math.sin(i*interval_theta*math.pi/180)            
            # r = xy_begin.y()-xy_center.y()
            # y = xy_center.y()+r*math.cos(i*interval_theta*math.pi/180)
            # x = xy_center.x()+r*math.sin(i*interval_theta*math.pi/180)
            xy_list.append(XY(x, y))
            
        # with safe_connection(_DEVICE_ID) as connection:
        builder = CommandBuilder()
        if down == True:
            builder.down(contact_id, xy_list[0].x(), xy_list[0].y(), pressure)
            builder.commit()
            builder.publish(self.device.connection)

        for i in range(1, num_points):
            # builder.wait(interval_time)
            builder.commit()
            builder.move(contact_id, xy_list[i].x(), xy_list[i].y(), pressure)
            builder.commit()
            builder.publish(self.device.connection)
        
        # builder.wait(time_consume)#temp
        if up == True:
            builder.up(contact_id)
            builder.commit()
            builder.publish(self.device.connection)


def get_xy():
    cmd = r'adb exec-out getevent -l /dev/input/event4' #r'adb shell getevent'
    try:
        p1=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        print("start")
        tmp = []
        count = 0 #触点总数量
        index = 0#0:第0个触点 1：第1个触点 ...
        x= 0
        y=0
        pattern_slot = re.compile(r'0000000\d')              
        pattern_position = re.compile(r'00000\w+')
        for line in p1.stdout:
            line = line.decode(encoding="utf-8", errors="ignore")
            if 'SYN_REPORT' in line:
                # print(tmp)
                flag = 0#0:无 1:按下 2：抬起
                
                for subline in tmp:
                    if "ABS_MT_TRACKING_ID" in subline:
                        if "ffffffff" in subline:
                            flag = 2#抬起
                        else:
                            flag = 1#按下
                    elif "ABS_MT_SLOT" in subline:
                        # print(subline)                        
                        a = pattern_slot.findall(subline)[0]
                        # a = subline.split(' ')
                        index = int(a)
                        # print(int(a))
                    elif "ABS_MT_POSITION_X" in subline:
                        b = pattern_position.findall(subline)[0]
                        x = int(b,16)
                    elif "ABS_MT_POSITION_Y" in subline:
                        b = pattern_position.findall(subline)[0]
                        y = int(b,16)
                # print(flag)
                if flag == 1:#按下
                    count+=1
                    print("tap count: ", count)
                    print("new down")
                    print("down tap index: ", index)
                    print("x: ", x)
                    print("y: ", y)
                    print("")
                elif flag == 2:#抬起
                    count-=1
                    print("tap count: ", count)
                    print("up")
                    print("up tap index: ", index)
                    print("")
                   
                tmp.clear()
            else:
                tmp.append(line)
            # print(line)

            # line = line.decode(encoding="utf-8", errors="ignore")
            # line = line.strip()
            # if ' 0035 ' in line:
            #     e = line.split(" ")
            #     w = e[3]
            #     w = int(w, 16)
                
            # if  ' 0036 ' in line:
            #     e = line.split(" ")
            #     h = e[3]
            #     h = int(h, 16)
            #     if h >0:
            #         p = (w, h) 
            #         count += 1                       
                    # print("count: ", count," ", p) 
        # p1.wait()

        # time.sleep(1)
    except Exception as e:
        print(e)


import signal
import subprocess
import re
from threading import Thread,Lock,Event 

class TouchStatus(object):
    def __init__(self, device, event_down, event_up):#, event_down, event_up
        self.device_ = device
        self.act_ = -1#-1:无 0:按下 1：抬起
        self.act_touch_index_=0
        self.interested_index_=-1
        self.x_ = 0
        self.y_= 0
        self.count_=0
        self.event_down_ = event_down
        self.event_up_ = event_up
    def process(self):
        # cmd = r'adb exec-out getevent -l /dev/input/event4'
        cmd = r'adb exec-out getevent -l '+self.device_
        try:
            p1=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
            pattern_slot = re.compile(r'0000000\d')              
            pattern_position = re.compile(r'00000\w+')
            line_group = []
            for line in p1.stdout:
                line = line.decode(encoding="utf-8", errors="ignore")
                if 'SYN_REPORT' in line:
                    # init
                    self.act_ = -1       
                    for subline in line_group:
                        if "ABS_MT_TRACKING_ID" in subline:
                            if "ffffffff" in subline :#and len(line_group) in [1,2, 3, 4]:
                                self.act_ = 1#抬起
                                self.count_-=1                            
                            else:#elif len(line_group) in [4, 5, 6]:
                                self.act_ = 0#按下
                                self.count_+=1
                        elif "ABS_MT_SLOT" in subline:          
                            a = pattern_slot.findall(subline)[0]
                            self.act_touch_index_ = int(a)
                        elif "ABS_MT_POSITION_X" in subline:
                            b = pattern_position.findall(subline)[0]
                            self.x_ = int(b,16)
                        elif "ABS_MT_POSITION_Y" in subline:
                            b = pattern_position.findall(subline)[0]
                            self.y_ = int(b,16)

                    # print(line_group)
                    line_group.clear()

                    if self.act_ == 0:#按下
                        if self.x_ <100 and self.y_>2200:                            
                            self.interested_index_ = self.act_touch_index_
                            self.event_down_.set()
                            print("act_: down")
                            print("act_touch_index_: ", self.act_touch_index_)
                            print("x: ", self.x_)
                            print("y: ", self.y_)
                            print("")
                            
                    elif self.act_ == 1:#抬起
                        if self.interested_index_ == self.act_touch_index_:                            
                            self.interested_index_ = -1
                            # self.event_up_.set()                           
                        # print("act_: up")
                        # print("act_touch_index_: ", self.act_touch_index_)
                        # print("")
                else:
                    line_group.append(line)
        except Exception as e:
            print(e)


def action_init():
    
    def action():
        global event_down, event_up
        
        minitouch = MiniTouch()
        contact_id = 4
        while True:
            # time.sleep(5)
            # minitouch.slice_line(contact_id, XY(335, 1825), XY(330, 1960), 0, down=True, up=False)
            # time.sleep(2)
            # angle = 90
            # minitouch.slice_circular(contact_id, XY(335, 1825), XY(335, 1960), angle, 1000, down=False, up=True)
                
            if event_down.is_set():
                print("get the event_down")
                minitouch.slice_line(contact_id, XY(335, 1825), XY(330, 1960), 0, down=True, up=False)
                
                time.sleep(2)
                # minitouch
                angle = 90                
                # angle = 180
                minitouch.slice_circular(contact_id, XY(335, 1825), XY(335, 1960), angle, 1000, down=False, up=True)
                
                event_down.clear()
            # elif event_up.is_set():
            #     print("get the event_up")

            #     # minitouch
            #     angle = 90                
            #     # angle = 180
            #     minitouch.slice_circular(contact_id, XY(335, 1825), XY(335, 1960), angle, 1000, down=False, up=True)
            #     event_up.clear()           
    t = Thread(target=action, name='action')
    t.start()

def touch_status_init(event_down, event_up):
    
    def action(event_down, event_up):
        touch_status = TouchStatus("/dev/input/event4", event_down, event_up)
        touch_status.process()

    t = Thread(target=action, args=(event_down, event_up), name='touch_status')
    t.start()

if __name__ == "__main__":
    # global event_down, event_up
    event_down = Event()
    event_up = Event()

    action_init()
    touch_status_init(event_down, event_up)

    time.sleep(100)
    # get_xy()
    # print(size)

    # minitouch = MiniTouch()
    # contact_id = 1
    # angle = 90
    # minitouch.slice_line(contact_id, XY(335, 1825), XY(335, 1960), 0, down=True, up=False)
    # time.sleep(1.8)
    # minitouch.slice_circular(contact_id, XY(335, 1825), XY(335, 1960), angle, 3000, down=False, up=True)
            

    # with safe_connection(_DEVICE_ID) as connection:
    #     contact_id = 1
    #     xy_center = XY(335, 1825)
    #     time_consume = 3000
    #     tap(contact_id, xy_center, time_consume, connection, down=True, up=True)

    #     contact_id = 0
    #     xy_begin = XY(330, 1860)
    #     xy_end = XY(330, 1960)
    #     time_consume = 2000
    #     slice_line(contact_id, xy_begin, xy_end, time_consume, connection, down=True, up=False)

    #     # contact_id = 1
    #     xy_center = XY(330, 1860)
    #     xy_begin = XY(330, 1960)
    #     time_consume = 2000
    #     angle = 180
    #     slice_circular(contact_id, xy_center, xy_begin, angle, time_consume, connection, down=False, up=True)
