# https://www.bing.com/HPImageArchive.aspx?format=xml&idx=0&n=1&mkt=en-IN
from xml.dom import minidom
from PIL import Image, ImageFilter
import io
import os
import ctypes
from time import sleep
import urllib3

blur = True

win = urllib3.PoolManager()
xin = win.request('GET', "http://www.bing.com/HPImageArchive.aspx?format=xml&idx=0&n=1&mkt=en-IN")
out = xin.data.decode('utf-8')

bing = minidom.parseString(out)
url = bing.getElementsByTagName("url")[0]
Img = ("http://www.bing.com" + url.firstChild.data).replace("1366x768", "1920x1080")

drive = "C:\\"
image = "1080.jpg"
image_path = os.path.join(drive, image)

img = win.request('GET', Img)
img = Image.open(io.BytesIO(img1080.data))


if blur:
    img.filter(ImageFilter.GaussianBlur(radius=5)).save(image_path, "JPEG", option='optimize')
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
    sleep(1)

img.save(image_path, "JPEG", option='optimize')
SPI_SETDESKWALLPAPER = 20
ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
exit(0)
