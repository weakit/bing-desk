# https://www.bing.com/HPImageArchive.aspx?format=xml&idx=0&n=1&mkt=en-IN
from xml.dom import minidom
from PIL import Image, ImageFilter
import io
import os
import ctypes
from time import sleep
import datetime

date = str(datetime.datetime.now()).split(' ')[0]
dates = open("C:\\Users\\Administrator\\dates.txt", 'a+')
dater = open("C:\\Users\\Administrator\\dates.txt", 'r')
if not str(dater.readlines()[0]) == date:
    dates.write("\n" + date)
    dates.close()

debug = False
legacy = False
burnable = True

if legacy:
    import urllib3
    win = urllib3.PoolManager()
    xin = win.request('GET', "http://www.bing.com/HPImageArchive.aspx?format=xml&idx=0&n=1&mkt=en-IN")
    out = xin.data.decode('utf-8')
else:
    import requests
    url = requests.get("http://www.bing.com/HPImageArchive.aspx?format=xml&idx=0&n=1&mkt=en-IN")
    out = url.text

bing = minidom.parseString(out)
url = bing.getElementsByTagName("url")[0]
Img = "http://www.bing.com" + url.firstChild.data
Img1080 = Img.replace("1366x768", "1920x1080")

drive = "C:\\"
image = "1080.jpg"
image_path = os.path.join(drive, image)

if debug:
    print(image_path)
    print(Img+"\n"+Img1080)
    if legacy:
        img = win.request('GET', Img)
    else:
        img = requests.get(Img)
    img = Image.open(io.BytesIO(img.data))
    img.save("C:\\lowres.jpg", "JPEG", option='optimize')

if legacy:
    img1080 = win.request('GET', Img1080)
    img1080 = Image.open(io.BytesIO(img1080.data))
else:
    img1080 = requests.get(Img1080, stream=True)
    img1080 = Image.open(img1080.raw)

if burnable:
    img1080.filter(ImageFilter.GaussianBlur(radius=5)).save(image_path, "JPEG", option='optimize')
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
    sleep(1)

img1080.save(image_path, "JPEG", option='optimize')
SPI_SETDESKWALLPAPER = 20
ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
exit(0)