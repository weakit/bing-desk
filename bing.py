import os
import json
import requests as r
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageFilter
from datetime import date, datetime
from xml.etree import ElementTree

# Settings
MARKET = 'en-IN'  # docs.microsoft.com/rest/api/cognitiveservices-bingsearch/bing-web-api-v7-reference#market-codes
BLUR = True  # Set this to false and pretend it doesn't exist (important)

# Not Settings
WINDOWS = False

# platform checks
if os.name.startswith('nt'):
    WINDOWS = True
    from ctypes import windll as win


def connected():
    req = r.head('http://example.com/')  # know a better site?
    if req.status_code == 200:
        return True
    return False


def change_setting(setting, value):
    content = list()
    if isinstance(value, str):
        value = f"'{value}'"
    with open(__file__, 'r') as f:
        for line in f:
            if line.startswith(f'{setting} = '):
                line = f"{setting} = {value}{''.join([' ' + x for x in line.split(' ')[3:]])}"
            content.append(line)
    with open(__file__, 'w') as f:
        for line in content:
            f.write(line)


def get_url(_id, n):
    return f'http://www.bing.com/HPImageArchive.aspx?format=xml&idx={_id}&n={n}&mkt={MARKET}'


def get_days_from_today(days: int):
    if days > 7:  # bing doesn't cache images for more than a week
        return None
    tree = ElementTree.fromstring(r.get(get_url(days, 1)).content)
    return parse_image(tree.find('image'))


def get_today():
    return get_days_from_today(0)


def get_date(d: date):
    days_from_today = (date.today() - d).days
    if days_from_today < 0:
        return None
    return get_days_from_today(days_from_today)


def parse_image(tree: ElementTree):
    image_url = f"https://bing.com{tree.find('url').text}"
    image_date_raw = tree.find('startdate').text
    image_date = f"{image_date_raw[:4]}-{image_date_raw[4:6]}-{image_date_raw[6:]}"
    headline = tree.find('headline').text
    _copyright = tree.find('copyright').text

    return {
        'image': image_url,
        'title': headline,
        'date': image_date,
        'copyright': _copyright,
    }


def cache_image(parsed_image: dict, image_filename='image.jpg', metadata_filename='meta.json',
                path=Path(Path.home(), Path('.bing-desk')), blur=BLUR):

    image = Image.open(BytesIO(r.get(parsed_image['image']).content))

    if not isinstance(path, Path):
        path = Path(path)
    if not path.is_dir():
        path.mkdir(parents=True, exist_ok=True)
        if WINDOWS:
            win.kernel32.SetFileAttributesW(str(path), 0x02)

    image_path = Path(path, Path(image_filename))
    image.save(str(image_path))

    if blur:
        blurred_image = image.filter(ImageFilter.BoxBlur(radius=4)).filter(ImageFilter.BoxBlur(radius=4))
        split_image_path = os.path.splitext(image_path)
        blurred_image.save(split_image_path[0] + '_blur' + split_image_path[1])

    metadata_path = Path(path, Path(metadata_filename))
    parsed_image.update({'fetched': str(datetime.now())})
    with metadata_path.open('wb') as file:
        file.write(json.dumps(parsed_image, ensure_ascii=False).encode('utf8'))

    return image_path, metadata_path


def set_windows_wallpaper(path: Path):
    win.user32.SystemParametersInfoW(20, 0, str(path), 3)


def change():
    parsed_image = get_today()
    image_path, metadata_path = cache_image(parsed_image)
    pass


if __name__ == '__main__':
    print(cache_image(get_today()))

