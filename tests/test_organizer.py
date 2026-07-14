import pytest

from mcp_file_organizer import mcp_server
from mcp_file_organizer.history import load_redo
from mcp_file_organizer.paths import resolve_in_workspace


def test_pdf_moves_to_documents(isolated_env):
    (isolated_env / "report.pdf").write_text("pdf content")

    mcp_server.organize_workspace()

    assert (isolated_env / "Documents" / "report.pdf").exists()
    assert not (isolated_env / "report.pdf").exists()


def test_jpg_moves_to_images(isolated_env):
    (isolated_env / "photo.jpg").write_text("jpg content")

    mcp_server.organize_workspace()

    assert (isolated_env / "Images" / "photo.jpg").exists()
    assert not (isolated_env / "photo.jpg").exists()


def test_collision_produces_numbered_suffix(isolated_env):
    existing_folder = isolated_env / "Docs"
    existing_folder.mkdir()
    (existing_folder / "a.txt").write_text("existing")
    (isolated_env / "a.txt").write_text("original")

    result = mcp_server.move_file("a.txt", "Docs")

    assert result["status"] == "ok"
    assert (existing_folder / "a.txt").read_text() == "existing"
    assert (existing_folder / "a(1).txt").read_text() == "original"


def test_path_escape_raises_valueerror(isolated_env):
    with pytest.raises(ValueError):
        resolve_in_workspace("../escaped.txt")

    assert not (isolated_env.parent / "escaped.txt").exists()


def test_undo_redo_round_trip_for_move_file(isolated_env):
    (isolated_env / "note.txt").write_text("note content")

    mcp_server.move_file("note.txt", "Documents")
    assert (isolated_env / "Documents" / "note.txt").exists()

    undo_result = mcp_server.undo_last_action()
    assert undo_result["status"] == "ok"
    assert (isolated_env / "note.txt").read_text() == "note content"
    assert not (isolated_env / "Documents" / "note.txt").exists()

    assert len(load_redo()) == 1

    redo_result = mcp_server.redo_last_action()
    assert redo_result["status"] == "ok"
    assert (isolated_env / "Documents" / "note.txt").exists()
    assert not (isolated_env / "note.txt").exists()
