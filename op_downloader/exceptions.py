from typing import Any


class ChapterNotFoundError(Exception):
    """Exception rised when downloading non-existing chapter."""

    def __init__(self, chapter: int, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.chapter = chapter

    def __str__(self) -> str:
        return f"chapter {self.chapter} is not available"
