import os
import numpy as np
import cv2
from PIL import Image

import sys   

def isNumber(s):
  try:
    int(s)
    return True
  except ValueError:
    return False

if len(sys.argv) != 4:          
    print('[Usage] python resizeImage.py [folderName] [width(int)] [height(int)]')
    exit(1)
elif not type(sys.argv[1]) is str : 
    print('[Usage] python resizeImage.py [folderName] [width(int)] [height(int)]')
    exit(1)
elif not isNumber(sys.argv[2]):
    print('[Usage] python resizeImage.py [folderName] [width(int)] [height(int)]')
    exit(1)
elif not isNumber(sys.argv[3]):
    print('[Usage] python resizeImage.py [folderName] [width(int)] [height(int)]')
    exit(1)
original_path = './' + sys.argv[1] +'/'
resized_path = './ResizedImages/' + sys.argv[1] + '/'
if not os.path.exists(resized_path):
    os.makedirs(resized_path)
file_list = os.listdir(original_path)
img_list = []

for item in file_list :
    if item.find('.png') is not -1 :
        img_list.append(item)

total_image = len(img_list)
index = 1
width = int(sys.argv[2])
height = int(sys.argv[3])

for name in img_list :

    img = Image.open('%s%s'%(original_path, name))
    img_array = np.array(img)
    img_resize = cv2.resize(img_array, (width, height), interpolation = cv2.INTER_AREA)
    img = Image.fromarray(img_resize)
    img.save('%s%s'%(resized_path, name))
    print(name + '   ' + str(index) + '/' + str(total_image))
    index = index + 1