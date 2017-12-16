import socket
import os
import ctypes
from PIL import Image, ImageFilter
from time import sleep
import datetime
# import pkgutil

unplugged = os.path.join("C:\\", "Windows", "Resources", "wall1.jpg")
image_path = os.path.join("C:\\", "1080.jpg")
blur = 0
debug = False
blurred = False

file = open("C:\\Users\\Administrator\\dates.txt", 'r')
x = file.readlines()[-1]
date = datetime.datetime(int(x[0:4]), int(x[5:7]), int(x[8:10]))
TooFar = False
if date + datetime.timedelta(days=6) <= datetime.datetime.now():
    TooFar = True


def seawall(img):
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, img, 3)


def plugged(host="8.8.8.8", port=53):
    try:
        socket.setdefaulttimeout(1)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        pass
    return False


if debug:
    print("Plugged? "+str(plugged()))

while True:
    if plugged():
        LastBlur = Image.open(image_path).filter(ImageFilter.GaussianBlur(radius=5))
        LastBlur.save(image_path)
        seawall(image_path)
        import Bing2Day

    else:
        if blur == 3:
            Image.open(unplugged).filter(ImageFilter.GaussianBlur(radius=5)).save(image_path)
            seawall(image_path)
        if blur == 6:
            if TooFar:
                Image.open(unplugged).save(image_path, "JPEG", option='optimize')
                seawall(image_path)
                exit(2)
            if not TooFar:
                seawall(image_path)
                exit(1)
        else:
            if not blurred:
                LastBlur = Image.open(image_path).filter(ImageFilter.GaussianBlur(radius=5))
                LastBlur.save(image_path)
                seawall(image_path)
                blurred = True
            sleep(1)
            blur += 1


