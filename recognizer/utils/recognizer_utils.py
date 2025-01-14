import numpy as np
import difflib
import cv2

def linear(data_x, data_y):
    m = len(data_y)
    x_bar = np.mean(data_x)
    sum_yx = 0
    sum_x2 = 0
    sum_delta = 0
    for i in range(m):
        x = data_x[i]
        y = data_y[i]
        sum_yx += y * (x - x_bar)
        sum_x2 += x ** 2
    # 根据公式计算w
    w = sum_yx / (sum_x2 - m * (x_bar ** 2))

    for i in range(m):
        x = data_x[i]
        y = data_y[i]
        sum_delta += (y - w * x)
    b = sum_delta / m
    return w, b

def get_string_similarity(string1, string2):
    return difflib.SequenceMatcher(None,string1,string2).ratio()

def split_img(img, box):
    (x_start, y_start), (x_end, y_end) = box
    return img[y_start:y_end, x_start:x_end, :]

def to_black_white(img, lim=250, gaussianblur=False):
    img = img.mean(axis=2).reshape((img.shape[0], img.shape[1], 1))
    img = (np.concatenate((img, img, img), axis=2) > lim)*255
    img = np.uint8(img)
    if gaussianblur:
        return cv2.GaussianBlur(img, (5,5), 0)
    return img

def to_better_timer(t: float):
    if t < 0.01:
        return "%.02f"%round(t*1000, 2)+"ms"
    elif t < 1:
        return "%s"%int(t*1000)+"ms"
    elif t < 10:
        return "%.02f"%round(t,2)+"s"
    else:
        return "%s"%int(t)+"s"

def matchshape(shape1, shape2):
    if len(shape1) != len(shape2):
        return False
    for i, k in zip(shape1, shape2):
        if i != k:
            return False
    return True