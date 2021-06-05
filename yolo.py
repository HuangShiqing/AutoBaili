import torch
import torch.nn as nn
from torch.autograd import Variable
import cv2
import numpy as np
import time
import random
import pickle as pkl

import sys

sys.path.append("./thirdparty/pytorch-yolo-v3")
darknet = __import__("thirdparty.pytorch-yolo-v3.darknet", fromlist=["Darknet"])
Darknet = darknet.Darknet
from util import *
from preprocess import prep_image, letterbox_image


class YoloNet:
    def __init__(self, cfg_path, weights_path, label):
        self._cfg_path = cfg_path
        self._weights_path = weights_path
        self._label = label
        self._num_classes = len(label)
        self._confidence_threshold = 0.5
        self._nms_threshold = 0.4
        self._CUDA = torch.cuda.is_available()
        self._net = None
        self._im_dim = None
        self._inp_dim = None

        print("Loading network.....")
        self._net = Darknet(self._cfg_path)
        self._net.load_weights(self._weights_path)
        print("Network successfully loaded")
        if self._CUDA:
            self._net.cuda()
        self._net.eval()
        self._inp_dim = int(self._net.net_info["height"])

    def prepare(self, orig_im):
        img = (letterbox_image(orig_im, (self._inp_dim, self._inp_dim)))#0.0015
        img_ = img.transpose((2, 0, 1))#0.000046
        # img_ = img[:,:,::-1].transpose((2,0,1)).copy()
        img_ = torch.from_numpy(img_).float().div(255.0).unsqueeze(0)#0.0013
        orig_ims = [orig_im]

        dim = orig_im.shape[1], orig_im.shape[0]
        self._im_dim = torch.FloatTensor(dim).repeat(1, 2)#0.00019
        if self._CUDA:#0.00085
            self._im_dim = self._im_dim.cuda()
            img_ = img_.cuda()
        return img_, orig_ims

    def inference(self, inp_data):
        with torch.no_grad():
            prediction = self._net(inp_data, self._CUDA)
        prediction = write_results(prediction, self._confidence_threshold, self._num_classes, nms=True,
                                   nms_conf=self._nms_threshold)
        # print("prediction: ", prediction)
        return prediction

    def deprepare(self, prediction):
        scaling_factor = torch.min(self._inp_dim / self._im_dim, dim=1)[0].view(-1, 1)
        prediction[:, [1, 3]] -= (self._inp_dim - scaling_factor * self._im_dim[:, 0].view(-1, 1)) / 2
        prediction[:, [2, 4]] -= (self._inp_dim - scaling_factor * self._im_dim[:, 1].view(-1, 1)) / 2
        prediction[:, 1:5] /= scaling_factor
        for i in range(prediction.shape[0]):
            prediction[i, [1, 3]] = torch.clamp(prediction[i, [1, 3]], 0.0, self._im_dim[i, 0])
            prediction[i, [2, 4]] = torch.clamp(prediction[i, [2, 4]], 0.0, self._im_dim[i, 1])
        return prediction.cpu().numpy()

    def write(self, x, results, out_jpg_path):
        c1 = tuple(x[1:3].int())
        c2 = tuple(x[3:5].int())
        img = results[int(x[0])]
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cls = int(x[-1])
        label = "{0}".format(self._label[cls])
        color = [255, 0, 0]
        cv2.cvtColor(ori_img, cv2.COLOR_BGR2RGB)
        cv2.rectangle(img, c1, c2, color, 1)
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1, 1)[0]
        c2 = c1[0] + t_size[0] + 3, c1[1] + t_size[1] + 4
        cv2.rectangle(img, c1, c2, color, -1)
        cv2.putText(img, label, (c1[0], c1[1] + t_size[1] + 4), cv2.FONT_HERSHEY_PLAIN, 1, [225, 255, 255], 1)
        cv2.imwrite(out_jpg_path, img)


if __name__ == '__main__':
    jpg_path = "./data/frame00000007.jpg"
    out_jpg_path = jpg_path.replace(".jpg", "_out.jpg")
    cfg_path = "./cfg/yolov3-tiny.cfg"
    weights_path = "./backup/yolov3-tiny_last.weights"
    label = ["enemy"]

    net = YoloNet(cfg_path, weights_path, label)
    ori_img = cv2.imread(jpg_path)
    ori_img = cv2.cvtColor(ori_img, cv2.COLOR_BGR2RGB)
    inp_data, orig_ims = net.prepare(ori_img)
    prediction_tmp = net.inference(inp_data)

    prediction = net.deprepare(prediction_tmp)
    # prediction : [[detect_index, x1, y1, x2, y2, ?, confidence, classes]]
    print("prediction: ", prediction)
    net.write(prediction[0], orig_ims, out_jpg_path)

    print("done")
    torch.cuda.empty_cache()

    exit()