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

def prepare(orig_im, inp_dim):
    # orig_im = cv2.imread(img)
    dim = orig_im.shape[1], orig_im.shape[0]
    img = (letterbox_image(orig_im, (inp_dim, inp_dim)))
    img_ = img.transpose((2,0,1)).copy()
    # img_ = img[:,:,::-1].transpose((2,0,1)).copy()
    img_ = torch.from_numpy(img_).float().div(255.0).unsqueeze(0)
    return img_, orig_im, dim

classes = ["enemy"]
def write(x, results):
    c1 = tuple(x[1:3].int())
    c2 = tuple(x[3:5].int())
    img = results[int(x[0])]
    cls = int(x[-1])
    label = "{0}".format(classes[cls])
    color = [255,0,0]
    cv2.rectangle(img, c1, c2,color, 1)
    t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1 , 1)[0]
    c2 = c1[0] + t_size[0] + 3, c1[1] + t_size[1] + 4
    cv2.rectangle(img, c1, c2,color, -1)
    cv2.putText(img, label, (c1[0], c1[1] + t_size[1] + 4), cv2.FONT_HERSHEY_PLAIN, 1, [225,255,255], 1)
    return img


class net:
    def __init__(self, cfg_path, weights_path, num_classes):
        # self.prediction = []
        self._cfg_path = cfg_path
        self._weights_path = weights_path
        self._num_classes = num_classes
        self._confidence_threshold = 0.5
        self._nms_threshold = 0.4

        print("Loading network.....")
        self._net = Darknet(self._cfg_path)
        self._net.load_weights(self._weights_path)
        print("Network successfully loaded")
        CUDA = torch.cuda.is_available()
        if CUDA:
            self._net.cuda()
        self._net.eval()
        self._inp_dim = int(self._net.net_info["height"])
    
    def inference(self, orig_im):
        # inp_data, orig_ims, im_dim = prep_image(jpg_path, inp_dim)
        inp_data, orig_ims, im_dim = prepare(orig_im, self._inp_dim)
        orig_ims = [orig_ims]
        im_dim = torch.FloatTensor(im_dim).repeat(1,2)
        CUDA = torch.cuda.is_available()
        if CUDA:
            im_dim = im_dim.cuda()
            inp_data = inp_data.cuda()
        with torch.no_grad():
            prediction = self._net(inp_data, CUDA)
        prediction = write_results(prediction, self._confidence_threshold, self._num_classes, nms = True, nms_conf = self._nms_threshold)

        scaling_factor = torch.min(self._inp_dim/im_dim, dim=1)[0].view(-1,1)
        prediction[:,[1,3]] -= (self._inp_dim - scaling_factor*im_dim[:,0].view(-1,1))/2
        prediction[:,[2,4]] -= (self._inp_dim - scaling_factor*im_dim[:,1].view(-1,1))/2
        prediction[:,1:5] /= scaling_factor
        for i in range(prediction.shape[0]):
            try:
                prediction[i, [1,3]] = torch.clamp(prediction[i, [1,3]], 0.0, im_dim[i,0])
                prediction[i, [2,4]] = torch.clamp(prediction[i, [2,4]], 0.0, im_dim[i,1]) 
            except:
                print("error in torch.clamp: ", prediction)  
        return  prediction.cpu().numpy()


if __name__ ==  '__main__':
    cfg_path = "./cfg/yolov3-tiny.cfg"
    weights_path = "./backup/yolov3-tiny_last.weights"
    jpg_path = "./data/frame.jpg"
    out_jpg_path = jpg_path.replace(".jpg", "_out.jpg")
    # out_jpg_path = jpg_path.split(".")[:-1]+"_out"+jpg_path.split(".")[-1]
    num_classes = 1
    confidence_threshold = 0.5
    nms_threshold = 0.4

    print("Loading network.....")
    model = Darknet(cfg_path)
    model.load_weights(weights_path)
    print("Network successfully loaded")

    CUDA = torch.cuda.is_available()
    if CUDA:
        model.cuda()
    model.eval()

    inp_dim = int(model.net_info["height"])
    inp_data, orig_ims, im_dim = prep_image(jpg_path, inp_dim)
    orig_ims = [orig_ims]
    im_dim = torch.FloatTensor(im_dim).repeat(1,2)
    if CUDA:
        im_dim = im_dim.cuda()
        inp_data = inp_data.cuda()
    # inp_data = get_test_input(inp_dim, CUDA)

    time_start = time.time()
    with torch.no_grad():
        prediction = model(inp_data, CUDA)
    
    prediction = write_results(prediction, confidence_threshold, num_classes, nms = True, nms_conf = nms_threshold)
    time_end = time.time()
    print("inference time: ", time_end - time_start)
    print("prediction: ", prediction)

    scaling_factor = torch.min(inp_dim/im_dim, dim=1)[0].view(-1,1)
    prediction[:,[1,3]] -= (inp_dim - scaling_factor*im_dim[:,0].view(-1,1))/2
    prediction[:,[2,4]] -= (inp_dim - scaling_factor*im_dim[:,1].view(-1,1))/2
    prediction[:,1:5] /= scaling_factor
    for i in range(prediction.shape[0]):
        prediction[i, [1,3]] = torch.clamp(prediction[i, [1,3]], 0.0, im_dim[i,0])
        prediction[i, [2,4]] = torch.clamp(prediction[i, [2,4]], 0.0, im_dim[i,1])    

    # prediction : [detect_index, x1, y1, x2, y2, ?, confidence, classes]
    print("prediction: ", prediction)

    to_save = write(prediction[0], orig_ims)
    cv2.imwrite("./data/frame_out.jpg", to_save)

    torch.cuda.empty_cache()