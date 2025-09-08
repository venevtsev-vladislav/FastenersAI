import os
import tempfile
import asyncio
from types import SimpleNamespace

import pytest
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.media_processor import MediaProcessor


class DummyFile:
    async def download_to_drive(self, path: str) -> None:
        with open(path, "wb") as f:
            f.write(b"data")


class DummyBot:
    async def get_file(self, file_id: str) -> DummyFile:  # type: ignore
        return DummyFile()


class DummyContext:
    def __init__(self) -> None:
        self.bot = DummyBot()


class DummyPhoto:
    file_id = "id"
    file_size = 10
    width = 1
    height = 1


class DummyVoice:
    file_id = "id"
    file_size = 10
    duration = 1


class DummyDocument:
    file_id = "id"
    file_size = 10
    file_name = "file.pdf"
    mime_type = "application/pdf"


def make_message(kind: str):
    if kind == "photo":
        return SimpleNamespace(photo=[DummyPhoto()], voice=None, document=None, caption="", content_type="photo")
    if kind == "voice":
        return SimpleNamespace(photo=[], voice=DummyVoice(), document=None, caption="", content_type="voice")
    if kind == "document":
        return SimpleNamespace(photo=[], voice=None, document=DummyDocument(), caption="", content_type="document")
    raise ValueError(kind)


@pytest.mark.parametrize("kind", ["photo", "voice", "document"])
def test_process_media_message_cleanup(kind: str):
    processor = MediaProcessor()
    context = DummyContext()
    message = make_message(kind)

    tmp_dir = tempfile.gettempdir()
    before = set(os.listdir(tmp_dir))
    result = asyncio.run(processor.process_media_message(message, context))
    after = set(os.listdir(tmp_dir))

    assert result is not None
    assert result["file_path"].startswith(tmp_dir)
    assert not os.path.exists(result["file_path"])
    assert before == after
    assert processor.temp_files == []
