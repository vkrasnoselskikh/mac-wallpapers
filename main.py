import argparse
import dataclasses
import datetime
import subprocess

import httpx
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from string import Formatter, Template

DEFAULT_PATH_DOWNLOAD = Path.home() / "Pictures" / "bing-wallpapers"

DEFAULT_PATH_DOWNLOAD.mkdir(exist_ok=True)

logger = logging.getLogger("bing-download")
logging.basicConfig(level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.ERROR)

@dataclasses.dataclass
class ImageInfo:
    id: str
    start_date: datetime.date
    url_base: str
    title: str


class ApiBingImage(httpx.Client):
    def __init__(self):
        super().__init__(base_url="https://www.bing.com")

    def get_image_info(self, days_before: int = None) -> ImageInfo:
        if days_before is None:
            days_before = 0

        resp = self.get(
            "/HPImageArchive.aspx", params={"format": "xml", "idx": days_before, "n": 1}
        )
        tree = ET.fromstring(resp.text)
        image_data = tree.find("image")
        url_base: str = image_data.find("urlBase").text
        date_str = image_data.find("startdate").text
        return ImageInfo(
            id=url_base.replace("/th?id=", ""),
            start_date=datetime.datetime.strptime(date_str, "%Y%m%d").date(),
            url_base=url_base,
            title=image_data.find("copyright").text,
        )

    def get_content_image(self, image_info: ImageInfo) -> bytes:
        _format = "_UHD.jpg"
        _url_image = image_info.url_base + _format
        resp = self.get(_url_image)
        return resp.content


def download_image(base_download_path: Path, days_before: int = None) -> Path:
    api = ApiBingImage()
    info = api.get_image_info(days_before=days_before)
    picture_name = info.id + ".jpg"
    image_path = base_download_path / picture_name
    logger.info(f"Download image: {info.title}")

    logger.info(f"To file: {image_path}")
    with open(image_path.absolute(), "wb") as f:
        f.write(api.get_content_image(info))
    return image_path


def set_image_to_mac_monitor(index_display: int, file_path):
    cmd_for_osascript = Template("""\
    set tlst to {}
        tell application "System Events"
            set tlst to a reference to every desktop
            set picture of item $MAC_DISPLAY of tlst to "$FILEPATH"
        end tell
    """).substitute(MAC_DISPLAY=index_display, FILEPATH=file_path)

    logger.debug(f"Set image to monitor: {index_display}")
    subprocess.run(f"osascript - << {cmd_for_osascript}", shell=True)


def cli():
    parser = argparse.ArgumentParser(
        description="Download images from Bing and set as wallpaper for Mac."
    )

    parser.add_argument(
        "--days-before", type=int, default=0, help="Days before image was in Bing"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=DEFAULT_PATH_DOWNLOAD,
        help="Path for downloading images",
    )

    parser.add_argument(
        "--display", type=int, default=1, help="Set image for display by order number."
    )

    args = parser.parse_args()

    image_path = download_image(args.base_path, args.days_before)
    if args.display:
        set_image_to_mac_monitor(args.display, image_path)


if __name__ == "__main__":
    cli()
