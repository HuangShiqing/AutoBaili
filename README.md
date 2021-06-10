# AutoBaili

这是一个能够实现王者荣耀百里守约自动狙击的小玩意. 目前能对各距离各角度的固定目标实现百分百的命中率. 正在优化代码提升对移动目标目标的命中率. 

![](./data/1.gif)
![](./data/2.gif)

## Videos
请一键三连!!!!!

## Requirements

我的硬件设备:

+ 小米9(安卓9)

+ Ubuntu 16.04

+ GTX 1080Ti

软件依赖:

+ scrcpy

+ gstreamer

+ minitouch

第三方库:

+ [ayooshkathuria](https://github.com/ayooshkathuria) / **[pytorch-yolo-v3](https://github.com/ayooshkathuria/pytorch-yolo-v3)**
+ [AlexeyAB](https://github.com/AlexeyAB) / **[darknet](https://github.com/AlexeyAB/darknet)**
+ [williamfzc](https://github.com/williamfzc) / **[pyminitouch](https://github.com/williamfzc/pyminitouch)**
## How to Run
**目前代码兼容性比较差. 敬请期待代码更新与教程更新**
+ Quick Start

```bash
git clone https://github.com/HuangShiqing/AutoBaili
git submodule update --init --recursive
python timi.py
```

## Tutorial from Scratch

1. [scrcpy: 将安卓屏幕投射到ubuntu主机]()(正在更新中)
2. [gstreamer python: 抓取处理与显示图像的流媒体框架]()(正在更新中)
3. [yolov3: labelImg标注darknet训练与python推理]()(正在更新中)
4. [adb: 安卓的触摸检测]()(正在更新中)
5. [minitouch: 安卓的触摸模拟]()(正在更新中)

## Updates & TODO

- [x] 05/30/2021: 实现射击固定靶
- [ ] 优化代码流程, 实现射击移动靶
- [ ] 优化触摸的检测与模拟
- [ ] 更换检测模型, 目标分三类: 低血量敌人, 中血量敌人, 高血量敌人
- [ ] 增加跟踪模块, 实现目标移动轨迹预测

## Community

![三维推活码](./data/Wechat.png)

微信交流群

## License

[Apache 2.0 license](https://github.com/PaddlePaddle/PaddleOCR/blob/master/LICENSE)

