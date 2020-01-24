import os
import json
import subprocess
import requests as r
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageFilter
from datetime import date, datetime
from xml.etree import ElementTree

# Settings
MARKET = 'en-IN'  # docs.microsoft.com/rest/api/cognitiveservices-bingsearch/bing-web-api-v7-reference#market-codes
BLUR = True  # Set this to false and pretend it doesn't exist (important)
HIRES = False  # Gets a slightly higher res (1920x1200 from 1920x1080) image BUT with the bing logo

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
    image_base = f"https://bing.com{tree.find('urlBase').text}"
    image_date_raw = tree.find('startdate').text
    image_date = f"{image_date_raw[:4]}-{image_date_raw[4:6]}-{image_date_raw[6:]}"
    headline = tree.find('headline').text
    _copyright = tree.find('copyright').text

    return {
        'image': image_url,
        'image_base': image_base,
        'title': headline,
        'date': image_date,
        'copyright': _copyright,
    }


def get_high_res(parsed_image):
    hi_res_url = parsed_image['image_base'] + "_1920x1200.jpg"
    res = r.get(hi_res_url)
    if res.status_code != 200:
        return Image.open(BytesIO(r.get(parsed_image['image']).content))
    return Image.open(BytesIO(res.content))


def cache_image(parsed_image: dict, image_filename='image.jpg', metadata_filename='meta.json',
                path=Path(Path.home(), Path('.bing-desk')), blur=BLUR):

    if HIRES:
        image = get_high_res(parsed_image)
    else:
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


def set_linux_wallpaper(path: Path):
    # adapted from https://stackoverflow.com/a/21213358
    # most are un-tested
    desktop_env = os.environ.get("DESKTOP_SESSION")
    try:
        if desktop_env in ["gnome", "unity", "cinnamon", "pantheon"]:
            uri = f"'file://{path}'"
            args = ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri]
            subprocess.Popen(args)

        elif desktop_env == "mate":
            try:  # MATE >= 1.6
                # http://wiki.mate-desktop.org/docs:gsettings
                args = ["gsettings", "set", "org.mate.background", "picture-filename", f"'{path}'"]
                subprocess.Popen(args)
            except FileNotFoundError:  # MATE < 1.6
                # https://bugs.launchpad.net/variety/+bug/1033918
                args = ["mateconftool-2", "-t", "string", "--set", "/desktop/mate/background/picture_filename",
                        f'"{path}"']
                subprocess.Popen(args)

        elif os.environ.get('GNOME_DESKTOP_SESSION_ID') and \
                "deprecated" not in os.environ.get('GNOME_DESKTOP_SESSION_ID'):  # gnome2
            # https://bugs.launchpad.net/variety/+bug/1033918
            args = ["gconftool-2", "-t", "string", "--set", "/desktop/gnome/background/picture_filename", f'"{path}"']
            subprocess.Popen(args)

        elif desktop_env in ["kde3", "trinity"] or os.environ.get('KDE_FULL_SESSION') == 'true':
            # http://ubuntuforums.org/archive/index.php/t-803417.html
            os.system(f'dcop kdesktop KBackgroundIface setWallpaper 0 "{path}" 6')

        elif "xfce" in desktop_env or desktop_env.startswith("xubuntu"):
            # http://www.commandlinefu.com/commands/view/2055/change-wallpaper-for-xfce4-4.6.0
            args0 = ["xfconf-query", "-c", "xfce4-desktop", "-p", "/backdrop/screen0/monitor0/image-path",
                     "-s", str(path)]
            args1 = ["xfconf-query", "-c", "xfce4-desktop", "-p", "/backdrop/screen0/monitor0/image-style", "-s", "3"]
            args2 = ["xfconf-query", "-c", "xfce4-desktop", "-p", "/backdrop/screen0/monitor0/image-show", "-s", "true"]
            args = ["xfdesktop", "--reload"]
            subprocess.Popen(args0)
            subprocess.Popen(args1)
            subprocess.Popen(args2)
            subprocess.Popen(args)

        elif desktop_env in ["fluxbox", "jwm", "openbox", "afterstep"]:
            # http://fluxbox-wiki.org/index.php/Howto_set_the_background
            try:
                args = ["fbsetbg", str(path)]
                subprocess.Popen(args)
            except FileNotFoundError:
                print("Try installing fbsetbg.")

        elif desktop_env == "icewm":
            # http://urukrama.wordpress.com/2007/12/05/desktop-backgrounds-in-window-managers/
            args = ["icewmbg", str(path)]
            subprocess.Popen(args)

        elif desktop_env == "blackbox":
            # http://blackboxwm.sourceforge.net/BlackboxDocumentation/BlackboxBackground
            args = ["bsetbg", "-full", str(path)]
            subprocess.Popen(args)

        elif desktop_env == "lxde" or desktop_env.startswith("lubuntu"):
            args = ["pcmanfm", "--set-wallpaper", str(path), "--wallpaper-mode=scaled"]
            subprocess.Popen(args, shell=True)

        elif desktop_env.startswith("wmaker"):
            # http://www.commandlinefu.com/commands/view/3857/set-wallpaper-on-windowmaker-in-one-line
            args = ["wmsetbg", "-s", "-u", str(path)]
            subprocess.Popen(args, shell=True)

        else:
            return None

    except Exception as e:
        if not isinstance(e, KeyboardInterrupt):
            return None

    return True


def change():
    parsed_image = get_today()
    image_path, metadata_path = cache_image(parsed_image)
    if WINDOWS:
        set_windows_wallpaper(image_path)
    else:
        set_linux_wallpaper(image_path)
    pass


if __name__ == '__main__':
    print(change())

