import hashlib
import io
import pytest
from scripts.setup import ensure_model


def test_checksum_failure_preserves_existing_file_and_cleans_partial(
    tmp_path, monkeypatch
):
    existing = tmp_path / "model.pt"
    existing.write_bytes(b"previous")
    item = {
        "file": "model.pt",
        "sha256": hashlib.sha256(b"expected").hexdigest(),
        "url": "https://example.invalid/model",
    }
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *a, **k: io.BytesIO(b"corrupt")
    )
    with pytest.raises(ValueError, match="Checksum mismatch"):
        ensure_model(item, tmp_path)
    assert existing.read_bytes() == b"previous"
    assert not list(tmp_path.glob("*.download"))
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *a, **k: io.BytesIO(b"expected")
    )
    assert ensure_model(item, tmp_path).read_bytes() == b"expected"


def test_offline_verification_never_downloads(tmp_path, monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("Network used in offline check")

    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    item = {
        "file": "model.pt",
        "sha256": hashlib.sha256(b"ok").hexdigest(),
        "url": "https://example.invalid/model",
    }
    with pytest.raises(ValueError):
        ensure_model(item, tmp_path, True)
    (tmp_path / "model.pt").write_bytes(b"ok")
    assert ensure_model(item, tmp_path, True).is_file()
