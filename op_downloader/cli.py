import asyncio
from pathlib import Path

import httpx
import typer

from op_downloader.downloader import ChaptersDownloader

_CHAPTERS_ARG = typer.Argument(
    ...,
    help=("Comma separated chapter numbers you want to download. The "
          "chapters list also support ranges. For examples, some valid "
          "chapter selections are: 1,2,3,4 or 1000,1005,1070-1077."))

_OUTPUT_OPT = typer.Option(Path("chapters"),
                           help="Output path for the downloaded chapters.")

app = typer.Typer()


@app.command()
def run(chapters: str = _CHAPTERS_ARG,
        ouptut_path: Path = _OUTPUT_OPT) -> None:
    all_chapters = _get_all_chapters(chapters)
    typer.echo("Downloading chapters:")
    typer.echo("\n".join(f"▶️ {o}" for o in all_chapters))
    asyncio.run(_run_downloader(all_chapters, ouptut_path))


def _get_all_chapters(chapters_selection: str) -> list[int]:
    all_chapters = []
    for chapter_sel in chapters_selection.split(","):
        chapter_sel = chapter_sel.strip()
        try:
            if "-" in chapter_sel:
                start, end = chapter_sel.split("-")
                all_chapters.extend(list(range(int(start), int(end) + 1)))
            else:
                all_chapters.append(int(chapter_sel))
        except ValueError:
            typer.echo(f"Invalid chapter selection: '{chapter_sel}'")
            raise typer.Abort()

    return all_chapters


async def _run_downloader(chapters: list[int], output_path: Path) -> None:
    async with httpx.AsyncClient() as client:
        cd = ChaptersDownloader(client, chapters_output_path=output_path)
        await cd.run(chapters)
