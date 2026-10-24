#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图片附件落盘测试"""

from converter.attachments import materialize_images


def test_local_image_copied_and_rewritten(tmp_path):
    src = tmp_path / "src" / "note.md"
    src.parent.mkdir()
    image = src.parent / "pic.png"
    image.write_bytes(b"fake-png-data")
    dest = tmp_path / "vault" / "inbox"
    dest.mkdir(parents=True)

    markdown, count = materialize_images(
        "![图](pic.png)", src, dest, "note-abc"
    )

    assert count == 1
    assert "attachments/note-abc/" in markdown
    files = list((dest / "attachments" / "note-abc").glob("*.png"))
    assert len(files) == 1
    assert files[0].read_bytes() == b"fake-png-data"


def test_repeated_image_counted_once(tmp_path):
    src = tmp_path / "src" / "note.md"
    src.parent.mkdir()
    (src.parent / "pic.png").write_bytes(b"data")
    dest = tmp_path / "inbox"
    dest.mkdir()

    markdown, count = materialize_images(
        "![一](pic.png)\n\n![二](pic.png)", src, dest, "note"
    )
    assert count == 1
    assert len(list((dest / "attachments" / "note").glob("*.png"))) == 1


def test_remote_image_unchanged(tmp_path):
    src = tmp_path / "note.md"
    src.write_text("x", encoding="utf-8")
    dest = tmp_path / "inbox"
    dest.mkdir()

    markdown, count = materialize_images(
        "![图](https://example.com/a.png)", src, dest, "note-abc"
    )

    assert count == 0
    assert markdown == "![图](https://example.com/a.png)"


def test_missing_image_unchanged(tmp_path):
    src = tmp_path / "note.md"
    src.write_text("x", encoding="utf-8")
    dest = tmp_path / "inbox"
    dest.mkdir()

    markdown, count = materialize_images("![图](missing.png)", src, dest, "note")
    assert count == 0
    assert markdown == "![图](missing.png)"


def test_outside_image_not_copied(tmp_path):
    src = tmp_path / "src" / "note.md"
    src.parent.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"secret")
    dest = tmp_path / "inbox"
    dest.mkdir()

    markdown, count = materialize_images(
        "![图](../outside.png)", src, dest, "note"
    )
    assert count == 0
    assert markdown == "![图](../outside.png)"
    assert not (dest / "attachments").exists()


def test_dry_run_does_not_copy(tmp_path):
    src = tmp_path / "src" / "note.md"
    src.parent.mkdir()
    (src.parent / "pic.png").write_bytes(b"data")
    dest = tmp_path / "inbox"
    dest.mkdir()

    markdown, count = materialize_images(
        "![图](pic.png)", src, dest, "note", dry_run=True
    )
    assert count == 1
    assert "attachments/note/" in markdown
    assert not (dest / "attachments").exists()
