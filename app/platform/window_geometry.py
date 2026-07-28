from __future__ import annotations


def visible_geometry(
    saved: dict | None,
    screens: list[dict],
    default: dict,
    minimum: tuple[int, int] = (640, 480),
    title_height: int = 40,
    keep_entire_window: bool = True,
) -> dict:
    if not screens:
        return dict(default)
    saved = saved or default
    width = max(minimum[0], int(saved.get("width", default["width"])))
    height = max(minimum[1], int(saved.get("height", default["height"])))
    x, y = int(saved.get("x", default["x"])), int(saved.get("y", default["y"]))

    target = None
    for screen in screens:
        horizontal = min(x + width, screen["x"] + screen["width"]) - max(x, screen["x"])
        title = min(y + title_height, screen["y"] + screen["height"]) - max(y, screen["y"])
        if horizontal >= min(80, width) and title >= min(title_height, height):
            target = screen
            break

    if target is None:
        target = screens[0]
        x = int(default["x"])
        y = int(default["y"])
    available_width = max(1, target["width"])
    available_height = max(1, target["height"])
    if available_width >= minimum[0]:
        width = min(width, available_width)
    if available_height >= minimum[1]:
        height = min(height, available_height)

    max_x = target["x"] + max(0, available_width - min(width, available_width))
    visible_height = height if keep_entire_window else min(title_height, available_height)
    max_y = target["y"] + max(0, available_height - min(visible_height, available_height))
    x = min(max(x, target["x"]), max_x)
    y = min(max(y, target["y"]), max_y)
    return {"x": x, "y": y, "width": width, "height": height}
