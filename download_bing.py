import argparse
import dataclasses
import datetime

import httpx
import xml.etree.ElementTree as ET
from pathlib import Path


@dataclasses.dataclass
class ImageInfo:
    id: str
    start_date: datetime.date
    url_base: str
    title: str


class ApiBingImage(httpx.Client):
    def __init__(self):
        super().__init__(base_url='https://www.bing.com')

    def get_image_info(self, days_before: int = None) -> ImageInfo:
        if days_before is None:
            days_before = 0

        resp = self.get('/HPImageArchive.aspx', params={
            'format': 'xml',
            'idx': days_before,
            'n': 1
        })
        tree = ET.fromstring(resp.text)
        image_data = tree.find('image')
        url_base: str = image_data.find('urlBase').text
        date_str = image_data.find('startdate').text
        return ImageInfo(
            id=url_base.replace('/th?id=', ''),
            start_date=datetime.datetime.strptime(date_str, '%Y%m%d').date(),
            url_base=url_base,
            title=image_data.find('copyright').text
        )

    def get_content_image(self, image_info: ImageInfo) -> bytes:
        _format = '_UHD.jpg'
        _url_image = image_info.url_base + _format
        resp = self.get(_url_image)
        return resp.content


def download_image(path: str, days_before: int = None) -> bytes:
    base_download_path = Path(__file__).parent
    api = ApiBingImage()
    info = api.get_image_info(days_before=4)
    picture_name = info.id + '.jpg'
    image_path = base_download_path / picture_name
    print(f"Download image: {info.title}. Picture_name: {picture_name}")

    with open(image_path, 'wb') as f:
        f.write(api.get_content_image(info))


def cli():
    parser = argparse.ArgumentParser(description='Download images from Bing.')

    parser.add_argument('--days-before', type=int,
                        default=0,
                        help='Days before image was in Bing')
    parser.add_argument('--base-path', type=Path, default=Path.cwd(), help='Path for downloading images')

    args = parser.parse_args()
    download_image(args.base_path, args.days_before)


if __name__ == '__main__':
    cli()
