import socket
import sys
import os
from PIL import Image, ImageFilter
import time
from datetime import datetime
from dateutil.parser import parse
import image

desperate = False
path = os.path.realpath('image.png')

if sys.platform.startswith('win'):
    import ctypes
    from PIL import ImageFilter
    platform = 'win'
elif sys.platform.startswith('linux'):
    platform = 'linux'
    import subprocess
else:
    exit(2)


def connected(host="8.8.8.8", port=53):
    # check dat net
    try:
        socket.setdefaulttimeout(1)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        pass
    return False


def restart():
    if desperate:
        en = os.environ.get('DESKTOP_SESSION')
        if en == 'pantheon':
            subprocess.Popen('gala --replace & disown', shell=True)
        if en == 'gnome':
            subprocess.Popen('gnome-shell --replace & disown', shell=True)
        if en == 'unity':
            subprocess.Popen('unity', shell=True)


def wall(img):
    if platform == 'win':
        ctypes.windll.user32.SystemParametersInfoW(20, 0, img, 3)
    elif platform == 'linux':
        subprocess.Popen(
            "DISPLAY=:0 GSETTINGS_BACKEND=dconf /usr/bin/gsettings set org.gnome.desktop.background picture-uri file://{0}"
            .format(img), shell=True)
        restart()


if __name__ == '__main__':
    tries = 0
    while tries < 3:
        if not connected():
            time.sleep(1)
            tries += 1
            continue
        if os.path.isfile(path):
            last = datetime.fromtimestamp(time.mktime(time.localtime(os.path.getmtime(path))))
            update = parse(image.getDates()[0])
            diff = update - last
            if diff.total_seconds() > 0:
                if platform == 'win':
                        # linux spoiled me
                        tmp_img = Image.open(path).filter(ImageFilter.GaussianBlur(radius=5))
                        tmp_img.save(path)
                        wall(path)
                        start = time.time()
                        img = image.getImage()
                        tmp_img = img.filter(ImageFilter.GaussianBlur(radius=5))
                        tmp_img.save(path)
                        end = time.time()
                        if end - start < 3:
                            time.sleep(3 - (end - start))
                        wall(path)
                        time.sleep(2)
                        img.save(path)
                        wall(path)
                elif platform == 'linux':
                    img = image.getImage()
                    img.save(path)
                    wall(path)
        else:
            img = image.getImage()
            img.save(path)
            wall(path)
        break
