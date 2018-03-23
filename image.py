from xml.dom import minidom
from PIL import Image, ImageFilter
import io
import os
import urllib3
import locale

base_URL = 'http://www.bing.com/HPImageArchive.aspx?format=xml&idx=0&n=1'
prefix_URL = '&mkt=en-IN'
URL = base_URL + prefix_URL
lib = urllib3.PoolManager()


def getImage():
    raw = lib.request('GET', URL).data.decode('utf-8')
    xml = minidom.parseString(raw)
    startdate = xml.getElementsByTagName('fullstartdate')[0].firstChild.data
    enddate = xml.getElementsByTagName('enddate')[0].firstChild.data
    img_urlBase = xml.getElementsByTagName('urlBase')[0]
    img_url = ("http://www.bing.com" + img_urlBase.firstChild.data + '_1920x1080.jpg')
    img = lib.request('GET', img_url)
    img = Image.open(io.BytesIO(img.data))
    return img


def getDates():
    raw = lib.request('GET', URL).data.decode('utf-8')
    xml = minidom.parseString(raw)
    startdate = xml.getElementsByTagName('fullstartdate')[0].firstChild.data
    enddate = xml.getElementsByTagName('enddate')[0].firstChild.data
    return (startdate, enddate)


if __name__ == '__main__':
    import time
    start = time.time()
    print(URL)
    image = getImage()
    image.save('image.png', 'PNG')
    print(getDates()[0], getDates()[1])
    end = time.time()
    print(end - start)
