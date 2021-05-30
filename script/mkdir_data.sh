#!/bin/bash
#Author:HuangShiqing
#Time:2021-05-19 18:08:04
#Name:mk_data_dir.sh
#Description:This is a awesome script.

read -e -p "src data dir: " SRC_DIR
read -e -p "dst data dir: " DST_DIR
mkdir -p ${DST_DIR}/Annotations/
mkdir -p ${DST_DIR}/ImageSets/Main
mkdir -p ${DST_DIR}/JPEGImages/
# ls ${OLD_DIR} |xargs mv ${DIR}/JPEGImages/
mv ${SRC_DIR}/*.jpg ${SRC_DIR}/*.png ${DST_DIR}/JPEGImages/ 
# > /dev/null
# labelImg ${DST_DIR}/JPEGImages/