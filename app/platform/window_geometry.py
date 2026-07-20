from __future__ import annotations


def visible_geometry(saved: dict | None, screens: list[dict], default: dict) -> dict:
    if not saved or not screens:
        return dict(default)
    width = max(640, int(saved.get("width", default["width"])))
    height = max(480, int(saved.get("height", default["height"])))
    x, y = int(saved.get("x", default["x"])), int(saved.get("y", default["y"]))
    for screen in screens:
        if x + 80 >= screen["x"] and x < screen["x"] + screen["width"] and y + 40 >= screen["y"] and y < screen["y"] + screen["height"]:
            return {"x": x, "y": y, "width": width, "height": height}
    primary = screens[0]
    return {"x": primary["x"] + 40, "y": primary["y"] + 40,
            "width": min(width, primary["width"] - 80), "height": min(height, primary["height"] - 80)}
