import asyncio
import io
import re
from pathlib import Path
from typing import Mapping, Optional, Sequence

import bs4
import httpx
from PIL import Image

BASE_URL = "https://onepiecechapters.com"


class ChaptersDownloader(object):
    """Downloads One Piece Chapters from TCB Scans.
    
    The chapters are stored in PDF format under the `chapters_output_path`.
    """

    def __init__(
            self,
            client: httpx.AsyncClient,
            chapters_output_path: Path = Path("chapters"),
    ) -> None:
        self.client = client
        self.chapters_output_path = chapters_output_path

    async def run(self, chapters: Sequence[int]) -> None:
        # Obtain URLs from the selected chapters
        all_chapters_urls = await self._get_chapters_urls()
        urls = [(chapter, all_chapters_urls[chapter]) for chapter in chapters]

        self.chapters_output_path.mkdir(parents=True, exist_ok=True)
        await asyncio.gather(*[self._process_chapter(*url) for url in urls])

    async def _get_chapters_urls(self) -> Mapping[int, str]:
        res = await self.client.get(f"{BASE_URL}/mangas/5/one-piece")
        soup = bs4.BeautifulSoup(res.content.decode(), "html.parser")
        chapter_anchors = soup.select(
            "div.overflow-hidden > div > div > div.col-span-2 > a")

        return {
            chapter: f'{BASE_URL}{a.attrs["href"]}'
            for a in chapter_anchors
            if (chapter := _get_chapter_number(a.attrs["href"].split("/")[-1]))
        }

    async def _process_chapter(self, chapter: int, url: str) -> None:
        # Runs the end 2 end for a single chapter

        # 1. Get all chapter HTML
        res = await self.client.get(url)

        # 2. Get all images present in the chapter page and download them
        im_urls = await self._parse_chapter_pages_urls(res.content.decode())
        ims = await asyncio.gather(
            *[self._download_image(im_url) for im_url in im_urls])

        # 3. Concatenate all images in a single PDF
        output_path = self.chapters_output_path / f"{chapter}.pdf"
        ims[0].save(output_path, save_all=True, append_images=ims[1:])

    async def _parse_chapter_pages_urls(self, html: str) -> list[str]:
        # Obtain Image urls of the chapter pages
        soup = bs4.BeautifulSoup(html, 'html.parser')
        return [im.attrs["src"] for im in soup.select("picture > img")]

    async def _download_image(self, url: str) -> Image.Image:
        # Download image and convert into an in-memory Pillow image
        res = await self.client.get(url)
        return Image.open(io.BytesIO(res.content)).convert("RGB")


def _get_chapter_number(s: str) -> Optional[int]:
    nums = re.findall(r"([0-9]+)", s)
    try:
        return int(nums[0])
    except ValueError:
        return None
