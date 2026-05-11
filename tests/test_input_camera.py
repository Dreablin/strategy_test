"""Input camera transform regression."""

import pygame

from game.camera import Camera
from game.input import screen_to_grid
from game.config import TILE_H, TILE_W
from game.iso import world_to_screen
from game.render import Renderer
from game.world import World


def test_screen_to_grid_roundtrip_with_camera_offset() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    camera = Camera((64, 32))
    gx, gy = 5, 5
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    screen_pos = (ox + sx + camera.offset[0] + TILE_W // 2, oy + sy + camera.offset[1] + TILE_H // 2)
    assert screen_to_grid(surface, world, screen_pos, camera) == (gx, gy)
