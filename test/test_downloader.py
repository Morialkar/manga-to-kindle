import asyncio
from pathlib import Path
from typing import Sequence

import httpx
import pytest

from op_downloader.downloader import ChaptersDownloader
from op_downloader.exceptions import ChapterNotFoundError


def test_download_runs_successfully(
        tempdir: Path, async_loop: asyncio.AbstractEventLoop) -> None:
    async_loop.run_until_complete(
        _async_download_chapters_runs_successfully(tempdir, [1, 10, 20, 50]))


def test_download_not_found_chapter(
        tempdir: Path, async_loop: asyncio.AbstractEventLoop) -> None:

    with pytest.raises(ChapterNotFoundError):
        async_loop.run_until_complete(
            _async_download_chapters_runs_successfully(tempdir, [9999999]))


async def _async_download_chapters_runs_successfully(
        tempdir: Path, chapters: Sequence[int]) -> None:
    async with httpx.AsyncClient() as client:
        cd = ChaptersDownloader(client, chapters_output_path=tempdir)
        chapter_paths = await cd.run(chapters)

    for cp in chapter_paths:
        assert cp.suffix == ".pdf"
        assert cp.exists() and cp.is_file()
