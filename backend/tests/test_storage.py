from io import BytesIO
from uuid import uuid4

import pytest

from app.integrations.storage import FileTooLarge, MediaStore


@pytest.mark.parametrize("key", ["../../.env", "/etc/passwd", "audio/../file.mp3", "audio/not-a-uuid.mp3", "audio/%2e%2e.mp3"])
def test_arbitrary_paths_are_not_resource_keys(tmp_path, key):
    with pytest.raises(ValueError):
        MediaStore(tmp_path).path_for(key)


def test_symbolic_directory_cannot_escape_root(tmp_path):
    root = tmp_path / "media"
    root.mkdir()
    (root / "audio").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        MediaStore(root).path_for(f"audio/{uuid4().hex}.mp3")


def test_oversized_stream_cleans_staging(tmp_path):
    store = MediaStore(tmp_path)
    with pytest.raises(FileTooLarge):
        with store.stage(BytesIO(b"12345"), 4):
            pytest.fail("No debe aceptar un stream excesivo")
    assert list((tmp_path / ".staging").iterdir()) == []
