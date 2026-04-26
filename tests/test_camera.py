"""Camera behavior tests (T45, expected RED until `game.camera` exists)."""

from game.camera import Camera


def test_initial_offset() -> None:
    c = Camera()
    assert c.offset == (0, 0)


def test_pan_accumulates() -> None:
    c = Camera()
    c.pan(10, 5)
    c.pan(-3, 1)
    assert c.offset == (7, 6)


def test_clamp_world_smaller_than_viewport() -> None:
    c = Camera()
    viewport = (1280, 720)
    bounds = (0, 0, 800, 600)
    c.pan(50, 50)
    c.clamp(viewport, bounds)
    cx = (viewport[0] - (bounds[2] - bounds[0])) // 2
    cy = (viewport[1] - (bounds[3] - bounds[1])) // 2
    assert c.offset == (cx, cy)
    c.pan(100, -100)
    c.clamp(viewport, bounds)
    assert c.offset == (cx, cy)


def test_clamp_world_larger_than_viewport() -> None:
    c = Camera()
    viewport = (800, 600)
    bounds = (0, 0, 2000, 2000)

    c.pan(10_000, 10_000)
    c.clamp(viewport, bounds)
    x, y = c.offset
    assert x <= -bounds[0]
    assert y <= -bounds[1]
    assert x + bounds[2] >= viewport[0]
    assert y + bounds[3] >= viewport[1]

    c.pan(-20_000, -20_000)
    c.clamp(viewport, bounds)
    x2, y2 = c.offset
    assert x2 <= -bounds[0]
    assert y2 <= -bounds[1]
    assert x2 + bounds[2] >= viewport[0]
    assert y2 + bounds[3] >= viewport[1]
