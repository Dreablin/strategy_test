"""2D camera offset with pan and clamp helpers."""


class Camera:
    """Stores a pixel offset and clamps viewport against world bounds."""

    __slots__ = ("_offset",)

    def __init__(self, initial_offset: tuple[int, int] = (0, 0)) -> None:
        self._offset = (int(initial_offset[0]), int(initial_offset[1]))

    @property
    def offset(self) -> tuple[int, int]:
        return self._offset

    def pan(self, dx: int, dy: int) -> None:
        ox, oy = self._offset
        self._offset = (ox + int(dx), oy + int(dy))

    def clamp(self, viewport_size: tuple[int, int], world_bounds_px: tuple[int, int, int, int]) -> None:
        vw, vh = viewport_size
        min_x, min_y, max_x, max_y = world_bounds_px
        world_w = max_x - min_x
        world_h = max_y - min_y
        ox, oy = self._offset

        if world_w <= vw:
            ox = (vw - world_w) // 2 - min_x
        else:
            lo_x = vw - max_x
            hi_x = -min_x
            ox = max(lo_x, min(hi_x, ox))

        if world_h <= vh:
            oy = (vh - world_h) // 2 - min_y
        else:
            lo_y = vh - max_y
            hi_y = -min_y
            oy = max(lo_y, min(hi_y, oy))

        self._offset = (ox, oy)
