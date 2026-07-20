from app.services.undo_service import UndoService


def test_undo_is_single_session_action():
    values = []
    undo = UndoService()
    undo.offer("Task completed", lambda: values.append("restored"))
    assert undo.undo()
    assert values == ["restored"]
    assert not undo.undo()
