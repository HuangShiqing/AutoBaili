import os
import random
import csv


def split_data(Root_dir, train_percent=0.8):
    Annotations_dir=os.path.join(Root_dir, "labels")
    ImageSetsMain_dir=os.path.join(Root_dir, "ImageSets/Main")
    JPEGImages_dir=os.path.join(Root_dir, "JPEGImages")

    train_list = []
    valid_list = []

    os.chdir(Annotations_dir)

    temp_list = []
    files = os.listdir(Annotations_dir)
    for file in files:
        if file in ['train.txt', 'val.txt']:
            continue
        if file[0] == '.':
            continue
        temp_list.append(file)
    random.shuffle(temp_list)
    threshold = int(len(temp_list) * train_percent)
    train_list += temp_list[0:threshold]
    valid_list += temp_list[threshold::]

    random.shuffle(train_list)
    random.shuffle(valid_list)

    with open(ImageSetsMain_dir+'/train.txt', 'w') as f:
        for path in train_list:
            f.write(path.strip().split('.')[0] + '\n')
    with open(ImageSetsMain_dir+'/val.txt', 'w') as f:
        for path in valid_list:
            f.write(path.strip().split('.')[0] + '\n')

    with open(Root_dir+'/train.txt', 'w') as f:
        for path in train_list:
            f.write(os.path.join(JPEGImages_dir, path.strip().split('.')[0]+".jpg") + '\n')
    with open(Root_dir+'/val.txt', 'w') as f:
        for path in valid_list:
            f.write(os.path.join(JPEGImages_dir, path.strip().split('.')[0]+".jpg") + '\n')
    print('Finished writing ')


def read_data(dir):
    x_train, y_train, x_valid, y_valid = [], [], [], []
    with open(dir + 'train.txt', 'r') as f:
        for line in f.readlines():
            x_train.append(line.strip().split(' ')[0])
            y_train.append(line.strip().split(' ')[1])
    with open(dir + 'val.txt', 'r') as f:
        for line in f.readlines():
            x_valid.append(line.strip().split(' ')[0])
            y_valid.append(line.strip().split(' ')[1])
    return x_train, y_train, x_valid, y_valid


if __name__ == '__main__':
    Root_dir = "/home/hsq/DeepLearning/data/timi/2021-05-19/"
#    Annotations_dir = "/home/hsq/DeepLearning/data/timi/2021-05-19/Annotations"
#    ImageSetsMain_dir = "/home/hsq/DeepLearning/data/timi/2021-05-19/ImageSets/Main"
#    if os.path.exists(os.path.join(ImageSetsMain_dir, 'train.txt')) or os.path.exists(os.path.join(ImageSetsMain_dir, 'val.txt')):
#        print('路径:', str(ImageSetsMain_dir), '下train.txt valid.txt文件存在，请手动删除后再运行该程序')
#        exit()

    split_data(Root_dir, train_percent=1)
    # x_train, y_train, x_valid, y_valid = read_data(Annotations_dir)
    exit()
