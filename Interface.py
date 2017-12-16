import socket
import os
import ctypes
from PIL import Image, ImageFilter
from time import sleep

image_path = os.path.join("C:\\", "1080.jpg")
blur = 0
blurred = False


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


while True:
    if plugged():
        LastBlur = Image.open(image_path).filter(ImageFilter.GaussianBlur(radius=5))
        LastBlur.save(image_path)
        seawall(image_path)
        import Bing2Day

    else:
        if blur == 6:
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


