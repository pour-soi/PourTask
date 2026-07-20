from app.platform.window_geometry import visible_geometry


def test_offscreen_window_returns_to_primary_without_resetting_size():
    saved = {"x": 4000, "y": 200, "width": 900, "height": 650}
    screens = [{"x": 0, "y": 0, "width": 1920, "height": 1080}]
    result = visible_geometry(saved, screens, {"x": 40, "y": 40, "width": 1060, "height": 700})
    assert result == {"x": 40, "y": 40, "width": 900, "height": 650}


def test_geometry_on_secondary_monitor_is_preserved():
    saved = {"x": 2100, "y": 100, "width": 800, "height": 600}
    screens = [{"x": 0, "y": 0, "width": 1920, "height": 1080},
               {"x": 1920, "y": 0, "width": 1920, "height": 1080}]
    assert visible_geometry(saved, screens, saved) == saved
