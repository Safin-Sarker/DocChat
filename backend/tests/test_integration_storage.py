"""Integration tests for StorageService — local filesystem mode with tmp_path."""

import pytest

from app.services.storage_service import StorageService


@pytest.fixture()
def storage(tmp_path, monkeypatch):
    """Create a StorageService in local mode pointing to tmp_path."""
    monkeypatch.setattr("app.services.storage_service.settings.USE_LOCAL_STORAGE", True)
    monkeypatch.setattr("app.services.storage_service.settings.LOCAL_STORAGE_PATH", str(tmp_path / "storage"))
    return StorageService()


@pytest.fixture()
def sample_file(tmp_path):
    """Create a small sample file to upload."""
    f = tmp_path / "sample.txt"
    f.write_text("hello world")
    return str(f)


@pytest.mark.asyncio
async def test_upload_file_local(storage, sample_file):
    path = await storage.upload_file(sample_file, "sample.txt", doc_id="d1", user_id="u1")
    assert "sample.txt" in path
    from pathlib import Path
    assert Path(path).exists()


@pytest.mark.asyncio
async def test_upload_file_creates_dirs(storage, sample_file):
    path = await storage.upload_file(sample_file, "deep.txt", doc_id="d2", user_id="u2")
    from pathlib import Path
    assert Path(path).parent.exists()


@pytest.mark.asyncio
async def test_delete_local(storage, sample_file):
    await storage.upload_file(sample_file, "to_delete.txt", doc_id="d3", user_id="u3")
    await storage.delete_document_files("d3", user_id="u3")
    from pathlib import Path
    doc_dir = storage.storage_path / "u3" / "d3"
    assert not doc_dir.exists()


@pytest.mark.asyncio
async def test_delete_nonexistent_local(storage):
    # Should not crash
    await storage.delete_document_files("nonexistent", user_id="uX")


@pytest.mark.asyncio
async def test_get_file_url_local(storage):
    url = storage.get_file_url("u1/d1/file.pdf")
    assert "file://" in url
    # On Windows, Path uses backslashes; normalise for the assertion
    assert "file.pdf" in url
