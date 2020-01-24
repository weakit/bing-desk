import os
import json
import time
import subprocess
import requests as r
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageFilter
from datetime import date, datetime
from xml.etree import ElementTree

# Settings
MARKET = 'en-US'  # docs.microsoft.com/rest/api/cognitiveservices-bingsearch/bing-web-api-v7-reference#market-codes
BLUR = False  # Set this to false and pretend it doesn't exist (important)
HIRES = False  # Gets a slightly higher res (1920x1200 from 1920x1080) image BUT with the bing logo

# Not Settings
WINDOWS = False

# platform checks
if os.name.startswith('nt'):
    WINDOWS = True
    from ctypes import windll as win


def connected():
    """Checks Internet Connection"""
    req = r.head('https://bing.com/')
    if req.status_code in [200, 301]:
        return True
    return False


def set_setting(setting, value, path=Path(Path.home(), Path('.bing-desk'))):
    """Sets a setting, and saves to disk"""
    settings_path = Path(path, 'settings.json')
    load_settings()
    if setting in ['MARKET', 'BLUR', 'HIRES']:
        globals()[setting] = value
    json.dump({'market': MARKET, 'blur': BLUR, 'hires': HIRES}, settings_path.open('w'))


def load_settings(path=Path(Path.home(), Path('.bing-desk'))):
    """Loads Settings from Disk"""
    settings_path = Path(path, 'settings.json')
    if not path.is_dir():
        path.mkdir(parents=True, exist_ok=True)
        if WINDOWS:
            win.kernel32.SetFileAttributesW(str(path), 0x02)
        json.dump({'market': MARKET, 'blur': BLUR, 'hires': HIRES}, settings_path.open('w'))

    if settings_path.is_file():
        _settings = json.load(settings_path.open('r'))
        for setting in _settings:
            if setting in ['market', 'blur', 'hires']:
                globals()[setting.upper()] = _settings[setting]  # I shouldn't be doing this but meh


def get_url(_id, n):
    """Generates an URL"""
    return f'http://www.bing.com/HPImageArchive.aspx?format=xml&idx={_id}&n={n}&mkt={MARKET}'


def get_days_from_today(days: int):
    if days > 7:  # bing doesn't cache images for more than a week
        return None
    tree = ElementTree.fromstring(r.get(get_url(days, 1)).content)
    return parse_image(tree.find('image'))


def get_today():
    """Gets the Image of the Day"""
    return get_days_from_today(0)


def get_date(d: date):
    """Gets the Image of the Day of a certain date"""
    days_from_today = (date.today() - d).days
    if days_from_today < 0:
        return None
    return get_days_from_today(days_from_today)


def parse_image(tree: ElementTree):
    """Parses XML"""
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
    """Gets the High-res version of an image"""
    hi_res_url = parsed_image['image_base'] + "_1920x1200.jpg"
    res = r.get(hi_res_url)
    if res.status_code != 200:
        return Image.open(BytesIO(r.get(parsed_image['image']).content))
    return Image.open(BytesIO(res.content))


def do_work(parsed_image: dict, image_filename='image.jpg', metadata_filename='meta.json',
            path=Path(Path.home(), Path('.bing-desk'))):
    """Does the work"""
    image_path = Path(path, Path(image_filename))
    split_image_path = os.path.splitext(image_path)

    if BLUR and path.is_dir():
        blurred_image_path = Path(split_image_path[0] + '_blur' + split_image_path[1])
        if blurred_image_path.is_file():
            set_wallpaper(blurred_image_path)

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

    if BLUR:  # Excessive, but I like it
        blurred_image = image.filter(ImageFilter.BoxBlur(radius=4)).filter(ImageFilter.BoxBlur(radius=4))
        blurred_image.save(str(blurred_image_path))
        set_wallpaper(blurred_image_path)
        time.sleep(.5)

    image.save(str(image_path))

    metadata_path = Path(path, Path(metadata_filename))
    parsed_image.update({'fetched': str(datetime.now())})
    with metadata_path.open('wb') as file:
        file.write(json.dumps(parsed_image, ensure_ascii=False).encode('utf8'))

    set_wallpaper(image_path)

    return image_path, metadata_path


def set_wallpaper(path: Path):
    """Sets the wallpaper"""
    if WINDOWS:
        return set_windows_wallpaper(path)
    return set_linux_wallpaper(path)


def set_windows_wallpaper(path: Path):
    """Sets the wallpaper on windows"""
    win.user32.SystemParametersInfoW(20, 0, str(path), 3)


def set_linux_wallpaper(path: Path):
    """Sets the wallpaper on linux"""
    # adapted from https://stackoverflow.com/a/21213358
    # most DEs are untested
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
            subprocess.Popen([f'dcop kdesktop KBackgroundIface setWallpaper 0 "{path}" 6'])

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


if __name__ == '__main__':
    import sys
    import argparse

    ver_info = sys.version_info

    if ver_info.major < 3 or ver_info.minor < 5:
        print("This version of Python is not supported.\nPlease upgrade to Python 3.5 or greater.")
        exit(0)

    parser = argparse.ArgumentParser(
        description="Change your wallpaper to Bing's Image of the Day.",
        epilog="https://github.com/weakit/bing-desktop"
    )

    load_settings()

    parser.add_argument('--market',
                        action='store',
                        help="Set your default market. See http://bit.ly/BingMarkets for a list of available markets."
                             f" Currently set to {MARKET}.")

    parser.add_argument('--hires',
                        action='store_true',
                        help=f'Toggle usage of the slightly higher res image.\nCurrently set to {HIRES}.')

    parser.add_argument('-s', '--silent',
                        action='store_true',
                        help="Don't print any info when changing wallpaper.")

    if WINDOWS:
        parser.add_argument('--blur',
                            action='store_true',
                            help=f'Toggle the "blur".\nCurrently set to {BLUR}.')
    namespace = parser.parse_args()

    if namespace.market is not None:
        set_setting('MARKET', namespace.market)
        print(f"Market set to {MARKET}.")
        exit()

    if namespace.blur:
        set_setting('BLUR', not BLUR)
        print("Blur " + ("enabled." if BLUR else "disabled."))
        exit()

    if namespace.hires:
        set_setting('HIRES', not HIRES)
        print("Hi-res image " + ("enabled." if HIRES else "disabled."))
        exit()

    if not connected():
        print("Not able to reach bing. Check your internet connection and try again.")
        exit()

    image_parsed = get_today()
    do_work(image_parsed)
    if not namespace.silent:
        print(f"Image changed successfully.\n{image_parsed['title']}\n{image_parsed['copyright']}")