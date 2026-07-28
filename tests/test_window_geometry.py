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


def test_partially_offscreen_geometry_is_clamped_into_work_area():
    saved = {"x": 1700, "y": 900, "width": 900, "height": 650}
    screens = [{"x": 0, "y": 0, "width": 1920, "height": 1040}]
    result = visible_geometry(
        saved, screens, {"x": 40, "y": 40, "width": 1300, "height": 780},
        minimum=(900, 620),
    )
    assert result == {"x": 1020, "y": 390, "width": 900, "height": 650}
    assert result["y"] + result["height"] <= 1040


def test_widget_offscreen_geometry_recovers_with_title_visible():
    saved = {"x": -5000, "y": -3000, "width": 280, "height": 180}
    screens = [{"x": 100, "y": 50, "width": 1200, "height": 800}]
    result = visible_geometry(
        saved, screens, {"x": 140, "y": 90, "width": 260, "height": 180},
        minimum=(220, 130),
        title_height=48,
        keep_entire_window=False,
    )
    assert result == {"x": 140, "y": 90, "width": 280, "height": 180}
