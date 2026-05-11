"""Asset loading with disk-first lookup and procedural fallbacks."""

import functools
import json
from pathlib import Path

import pygame

from game.config import TILE_H, TILE_W

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ASSETS_ROOT = _PROJECT_ROOT / "assets"
_BUILDINGS_ROOT = _ASSETS_ROOT / "buildings"
_TREES_ROOT = _ASSETS_ROOT / "trees"
_WORLD_ROOT = _ASSETS_ROOT / "world"
_STONE_ROOT = _WORLD_ROOT / "stone"
_IRON_ROOT = _WORLD_ROOT / "iron"
_GOLD_ROOT = _WORLD_ROOT / "gold"
_NPC_ROOT = _ASSETS_ROOT / "npc"
_ICONS_ROOT = _ASSETS_ROOT / "icons"
_UI_ROOT = _ASSETS_ROOT / "ui"

_BUILDING_FOLDER: dict[str, str] = {
    "TOWN_HALL": "town_hall",
    "LUMBER_CAMP": "lumber_camp",
    "STONE_MINE": "stone_mine",
    "IRON_MINE": "iron_mine",
    "FARM": "farm",
    "FIELD": "field",
    "FORESTER_HUT": "forester_hut",
    "SCHOOL": "school",
    "HOUSE": "house",
    "CANTEEN": "canteen",
    "MILL": "windmill",
    "BAKERY": "bakery",
    "CHICKEN_FARM": "chicken_farm",
    "COW_FARM": "cow_farm",
    "WELL": "well",
}

_WORKER_FOLDER: dict[str, str] = {
    "LUMBERJACK": "lumberjack",
    "STONECUTTER": "stonecutter",
    "MINER": "miner",
    "FARMER": "farmer",
    "ANIMAL_HERDER": "animal_herder",
    "FORESTER": "forester",
    "CARRIER": "carrier",
    "BUILDER": "builder",
    "SAWYER": "sawyer",
    "MILLER": "miller",
    "BAKER": "baker",
    "COOK": "cook",
    "WATERMAN": "waterman",
}


def _diamond_points(w: int, h: int) -> list[tuple[int, int]]:
    return [(w // 2, 0), (w - 1, h // 2), (w // 2, h - 1), (0, h // 2)]


def _building_folder_name(b_type: str) -> str:
    t = b_type.upper().replace(" ", "_")
    return _BUILDING_FOLDER.get(t, t.lower())


@functools.lru_cache(maxsize=1)
def grass_tile() -> pygame.Surface:
    """Grass tile is still procedural for now."""
    surf = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
    pts = _diamond_points(TILE_W, TILE_H)
    pygame.draw.polygon(surf, (72, 152, 84), pts)
    pygame.draw.polygon(surf, (36, 92, 44), pts, 1)
    return surf


def _procedural_tree_sprite(stage: str, species: int = 0) -> pygame.Surface:
    """Fallback tall tree sprite used when no staged asset exists."""
    w, h = 48, 72
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    species_palettes: dict[int, dict[str, tuple[int, int, int]]] = {
        0: {
            "sapling": (125, 195, 115),
            "young": (88, 168, 92),
            "mature": (58, 138, 78),
            "adult": (36, 108, 62),
        },
        1: {
            "sapling": (170, 196, 116),
            "young": (140, 172, 92),
            "mature": (108, 148, 78),
            "adult": (84, 124, 62),
        },
        2: {
            "sapling": (126, 184, 170),
            "young": (94, 160, 142),
            "mature": (72, 136, 120),
            "adult": (56, 112, 100),
        },
    }
    palette = species_palettes.get(species, species_palettes[0])
    canopy = palette.get(stage, (58, 138, 78))
    trunk_x = w // 2 - 3
    pygame.draw.rect(surf, (86, 52, 28), (trunk_x, h - 24, 6, 24))
    pygame.draw.circle(surf, canopy, (w // 2, h - 36), 16)
    pygame.draw.circle(surf, (20, 56, 30), (w // 2, h - 36), 16, 1)
    return surf


def tree_sprite(stage: str, species: int = 0) -> pygame.Surface:
    """Load species+stage tree sprite from disk, fallback to procedural."""
    return _tree_render_spec(stage, species)[0]


def tree_sprite_anchor(stage: str, species: int = 0) -> tuple[int, int]:
    """Return anchor pixel in tree sprite (x,y)."""
    return _tree_render_spec(stage, species)[1]


def tree_sprite_offset(stage: str, species: int = 0) -> tuple[int, int]:
    """Return render offset in pixels for tree sprite (dx,dy)."""
    return _tree_render_spec(stage, species)[2]


@functools.lru_cache(maxsize=32)
def _tree_render_spec(stage: str, species: int = 0) -> tuple[pygame.Surface, tuple[int, int], tuple[int, int]]:
    """Load tree sprite, anchor and offset from assets/meta, fallback to procedural defaults."""
    stage_key = str(stage).lower().strip()
    if "." in stage_key:
        stage_key = stage_key.split(".")[-1]
    species_key = int(species)
    loaded = _load_png(str(_TREES_ROOT / f"species_{species_key}" / stage_key / "default.png"))
    src = loaded if loaded is not None else _procedural_tree_sprite(stage_key, species_key)
    meta = _tree_meta_for(species_key, stage_key)
    return _apply_tree_meta(src, meta)


def _procedural_stone_sprite(variant: int = 0) -> pygame.Surface:
    """Fallback stone pile sprite when no disk asset is present."""
    w, h = 42, 26
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = w // 2
    base = [(mid, 2), (w - 3, h // 2), (mid, h - 3), (3, h // 2)]
    palettes = [
        ((142, 146, 154), (76, 80, 92), (170, 174, 182), (124, 128, 138)),
        ((154, 146, 138), (92, 80, 72), (182, 174, 166), (138, 128, 120)),
        ((136, 152, 148), (72, 92, 86), (166, 182, 176), (120, 138, 132)),
        ((148, 140, 160), (84, 76, 100), (176, 168, 190), (132, 124, 146)),
        ((158, 154, 136), (96, 92, 74), (186, 182, 162), (142, 138, 118)),
    ]
    fill, outline, top_a, top_b = palettes[int(variant) % len(palettes)]
    pygame.draw.polygon(surf, fill, base)
    pygame.draw.polygon(surf, outline, base, 1)
    pygame.draw.circle(surf, top_a, (mid - 6, h // 2 - 3), 5)
    pygame.draw.circle(surf, top_b, (mid + 5, h // 2 + 1), 4)
    return surf


def _procedural_iron_sprite(variant: int = 0, *, blocking: bool) -> pygame.Surface:
    w, h = (54, 34) if blocking else (36, 22)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = w // 2
    base = [(mid, 1), (w - 3, h // 2), (mid, h - 3), (3, h // 2)]
    if blocking:
        palettes = [
            ((58, 48, 52), (170, 92, 74)),
            ((64, 54, 56), (185, 110, 82)),
            ((48, 52, 58), (150, 100, 96)),
            ((70, 48, 44), (200, 120, 80)),
            ((52, 44, 50), (160, 82, 92)),
        ]
    else:
        palettes = [
            ((92, 78, 72), (205, 132, 92)),
            ((86, 82, 84), (190, 116, 104)),
            ((76, 76, 82), (178, 122, 116)),
            ((96, 70, 62), (214, 142, 88)),
            ((80, 70, 76), (184, 98, 110)),
        ]
    dark, bright = palettes[max(0, min(4, int(variant)))]
    pygame.draw.polygon(surf, dark, base)
    pygame.draw.polygon(surf, bright, [(mid, 4), (w - 10, h // 2), (mid + 2, h - 8), (9, h // 2)])
    pygame.draw.line(surf, (238, 178, 122), (mid - 8, h // 2), (mid + 8, h // 2 - 2), 2)
    return surf


def _procedural_gold_sprite(variant: int = 0, *, blocking: bool) -> pygame.Surface:
    w, h = (54, 34) if blocking else (36, 22)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = w // 2
    base = [(mid, 1), (w - 3, h // 2), (mid, h - 3), (3, h // 2)]
    if blocking:
        palettes = [
            ((70, 58, 38), (226, 174, 74)),
            ((76, 62, 42), (238, 188, 86)),
            ((62, 58, 46), (210, 164, 88)),
            ((82, 66, 38), (246, 198, 82)),
            ((68, 54, 42), (220, 152, 66)),
        ]
    else:
        palettes = [
            ((112, 88, 52), (245, 196, 82)),
            ((104, 90, 58), (230, 182, 92)),
            ((98, 84, 62), (218, 176, 104)),
            ((122, 88, 46), (252, 210, 88)),
            ((108, 78, 52), (232, 164, 72)),
        ]
    dark, bright = palettes[max(0, min(4, int(variant)))]
    pygame.draw.polygon(surf, dark, base)
    pygame.draw.polygon(surf, bright, [(mid, 4), (w - 10, h // 2), (mid + 2, h - 8), (9, h // 2)])
    pygame.draw.line(surf, (255, 232, 142), (mid - 8, h // 2), (mid + 8, h // 2 - 2), 2)
    return surf


def stone_sprite(variant: int = 0) -> pygame.Surface:
    """Load stone world sprite by variant, fallback to procedural."""
    return _stone_render_spec(variant)[0]


def stone_sprite_anchor(variant: int = 0) -> tuple[int, int]:
    """Return anchor pixel in stone sprite (x,y)."""
    return _stone_render_spec(variant)[1]


def stone_sprite_offset(variant: int = 0) -> tuple[int, int]:
    """Return render offset in pixels for stone sprite (dx,dy)."""
    return _stone_render_spec(variant)[2]


def iron_sprite(variant: int = 0, *, blocking: bool = False) -> pygame.Surface:
    return _iron_render_spec(variant, blocking)[0]


def iron_sprite_anchor(variant: int = 0, *, blocking: bool = False) -> tuple[int, int]:
    return _iron_render_spec(variant, blocking)[1]


def iron_sprite_offset(variant: int = 0, *, blocking: bool = False) -> tuple[int, int]:
    return _iron_render_spec(variant, blocking)[2]


def gold_sprite(variant: int = 0, *, blocking: bool = False) -> pygame.Surface:
    return _gold_render_spec(variant, blocking)[0]


def gold_sprite_anchor(variant: int = 0, *, blocking: bool = False) -> tuple[int, int]:
    return _gold_render_spec(variant, blocking)[1]


def gold_sprite_offset(variant: int = 0, *, blocking: bool = False) -> tuple[int, int]:
    return _gold_render_spec(variant, blocking)[2]


@functools.lru_cache(maxsize=16)
def _stone_render_spec(variant: int = 0) -> tuple[pygame.Surface, tuple[int, int], tuple[int, int]]:
    variant_key = max(0, min(4, int(variant)))
    loaded = _load_png(str(_STONE_ROOT / f"species_{variant_key}" / "default.png"))
    if loaded is None:
        loaded = _load_png(str(_STONE_ROOT / "default.png"))
    src = loaded if loaded is not None else _procedural_stone_sprite(variant_key)
    meta = _stone_meta_for(variant_key)
    return _apply_stone_meta(src, meta)


@functools.lru_cache(maxsize=32)
def _iron_render_spec(variant: int = 0, blocking: bool = False) -> tuple[pygame.Surface, tuple[int, int], tuple[int, int]]:
    variant_key = max(0, min(4, int(variant)))
    folder = "blocking" if blocking else "buildable"
    loaded = _load_png(str(_IRON_ROOT / folder / f"species_{variant_key}" / "default.png"))
    if loaded is None:
        loaded = _load_png(str(_IRON_ROOT / folder / "default.png"))
    src = loaded if loaded is not None else _procedural_iron_sprite(variant_key, blocking=blocking)
    meta = _iron_meta_for(variant_key, blocking=blocking)
    return _apply_stone_meta(src, meta)


@functools.lru_cache(maxsize=32)
def _gold_render_spec(variant: int = 0, blocking: bool = False) -> tuple[pygame.Surface, tuple[int, int], tuple[int, int]]:
    variant_key = max(0, min(4, int(variant)))
    folder = "blocking" if blocking else "buildable"
    loaded = _load_png(str(_GOLD_ROOT / folder / f"species_{variant_key}" / "default.png"))
    if loaded is None:
        loaded = _load_png(str(_GOLD_ROOT / folder / "default.png"))
    src = loaded if loaded is not None else _procedural_gold_sprite(variant_key, blocking=blocking)
    meta = _gold_meta_for(variant_key, blocking=blocking)
    return _apply_stone_meta(src, meta)


def _building_palette(b_type: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    t = b_type.lower().replace(" ", "_")
    palettes: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
        "town_hall": ((180, 160, 120), (90, 70, 50)),
        "lumber_camp": ((120, 90, 60), (60, 45, 30)),
        "stone_mine": ((140, 140, 150), (70, 70, 80)),
        "iron_mine": ((150, 110, 100), (80, 55, 50)),
        "farm": ((170, 150, 90), (90, 120, 60)),
        "forester_hut": ((126, 112, 78), (68, 86, 54)),
        "mill": ((210, 190, 150), (112, 88, 58)),
        "bakery": ((214, 154, 118), (126, 72, 58)),
        "chicken_farm": ((186, 170, 110), (96, 82, 54)),
        "cow_farm": ((150, 118, 88), (78, 56, 40)),
        "well": ((104, 128, 152), (48, 70, 92)),
        "school": ((120, 124, 168), (62, 66, 108)),
        "house": ((172, 142, 126), (110, 86, 76)),
        "canteen": ((168, 132, 102), (92, 68, 48)),
    }
    return palettes.get(t, ((120, 120, 130), (60, 60, 70)))


@functools.lru_cache(maxsize=512)
def _load_png_by_mtime(path_s: str, mtime_ns: int) -> pygame.Surface | None:
    _ = mtime_ns
    path = Path(path_s)
    if not path.exists():
        return None
    try:
        img = pygame.image.load(str(path))
    except pygame.error:
        return None
    # convert_alpha is ideal but needs display mode; keep robust for tests/tools.
    try:
        return img.convert_alpha()
    except pygame.error:
        return img


def _load_png(path_s: str) -> pygame.Surface | None:
    path = Path(path_s)
    if not path.exists():
        return None
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return None
    return _load_png_by_mtime(path_s, mtime_ns)


@functools.lru_cache(maxsize=1)
def _load_tree_meta() -> dict:
    """Read tree asset meta once; refresh via clear_asset_caches()."""
    path = _TREES_ROOT / "asset_meta.json"
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


@functools.lru_cache(maxsize=1)
def _load_stone_meta() -> dict:
    path = _STONE_ROOT / "asset_meta.json"
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


@functools.lru_cache(maxsize=1)
def _load_iron_meta() -> dict:
    path = _IRON_ROOT / "asset_meta.json"
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


@functools.lru_cache(maxsize=1)
def _load_gold_meta() -> dict:
    path = _GOLD_ROOT / "asset_meta.json"
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _stone_meta_for(variant: int) -> dict:
    meta = _load_stone_meta()
    out: dict = {}
    default = meta.get("default")
    if isinstance(default, dict):
        out.update(default)
    variants = meta.get("variants")
    if isinstance(variants, dict):
        cfg = variants.get(str(variant))
        if isinstance(cfg, dict):
            out.update(cfg)
    return out


def _iron_meta_for(variant: int, *, blocking: bool) -> dict:
    meta = _load_iron_meta()
    group_key = "blocking" if blocking else "buildable"
    group = meta.get(group_key)
    if not isinstance(group, dict):
        group = {}
    out: dict = {}
    default = group.get("default") or meta.get("default")
    if isinstance(default, dict):
        out.update(default)
    variants = group.get("variants")
    if isinstance(variants, dict):
        cfg = variants.get(str(variant))
        if isinstance(cfg, dict):
            out.update(cfg)
    return out


def _gold_meta_for(variant: int, *, blocking: bool) -> dict:
    meta = _load_gold_meta()
    group_key = "blocking" if blocking else "buildable"
    group = meta.get(group_key)
    if not isinstance(group, dict):
        group = {}
    out: dict = {}
    default = group.get("default") or meta.get("default")
    if isinstance(default, dict):
        out.update(default)
    variants = group.get("variants")
    if isinstance(variants, dict):
        cfg = variants.get(str(variant))
        if isinstance(cfg, dict):
            out.update(cfg)
    return out


def _apply_stone_meta(src: pygame.Surface, meta: dict) -> tuple[pygame.Surface, tuple[int, int], tuple[int, int]]:
    scale_raw = meta.get("scale", 1.0)
    try:
        scale = float(scale_raw)
    except (TypeError, ValueError):
        scale = 1.0
    if scale <= 0:
        scale = 1.0
    if scale != 1.0:
        sw = max(1, int(round(src.get_width() * scale)))
        sh = max(1, int(round(src.get_height() * scale)))
        src = pygame.transform.smoothscale(src, (sw, sh))

    ax = src.get_width() // 2
    ay = src.get_height()
    anchor_norm = meta.get("anchor_norm")
    if isinstance(anchor_norm, (list, tuple)) and len(anchor_norm) == 2:
        try:
            nx = float(anchor_norm[0])
            ny = float(anchor_norm[1])
            ax = int(round(nx * src.get_width()))
            ay = int(round(ny * src.get_height()))
        except (TypeError, ValueError):
            pass

    dx, dy = 0, 0
    offset_px = meta.get("offset_px")
    if isinstance(offset_px, (list, tuple)) and len(offset_px) == 2:
        try:
            dx = int(round(float(offset_px[0])))
            dy = int(round(float(offset_px[1])))
        except (TypeError, ValueError):
            dx, dy = 0, 0
    ax = max(0, min(src.get_width(), ax))
    ay = max(0, min(src.get_height(), ay))
    return src, (ax, ay), (dx, dy)


def _tree_meta_for(species: int, stage_key: str) -> dict:
    meta = _load_tree_meta()
    out: dict = {}
    default = meta.get("default")
    if isinstance(default, dict):
        out.update(default)
    stages = meta.get("stages")
    if isinstance(stages, dict):
        stage_cfg = stages.get(stage_key)
        if isinstance(stage_cfg, dict):
            out.update(stage_cfg)
    species_map = meta.get("species")
    if isinstance(species_map, dict):
        sp_cfg = species_map.get(str(species))
        if isinstance(sp_cfg, dict):
            sp_default = sp_cfg.get("default")
            if isinstance(sp_default, dict):
                out.update(sp_default)
            sp_stages = sp_cfg.get("stages")
            if isinstance(sp_stages, dict):
                sp_stage_cfg = sp_stages.get(stage_key)
                if isinstance(sp_stage_cfg, dict):
                    out.update(sp_stage_cfg)
    return out


def _apply_tree_meta(src: pygame.Surface, meta: dict) -> tuple[pygame.Surface, tuple[int, int], tuple[int, int]]:
    scale_raw = meta.get("scale", 1.0)
    try:
        scale = float(scale_raw)
    except (TypeError, ValueError):
        scale = 1.0
    if scale <= 0:
        scale = 1.0
    if scale != 1.0:
        sw = max(1, int(round(src.get_width() * scale)))
        sh = max(1, int(round(src.get_height() * scale)))
        src = pygame.transform.smoothscale(src, (sw, sh))

    ax = src.get_width() // 2
    ay = src.get_height()
    anchor_norm = meta.get("anchor_norm")
    if isinstance(anchor_norm, (list, tuple)) and len(anchor_norm) == 2:
        try:
            nx = float(anchor_norm[0])
            ny = float(anchor_norm[1])
            ax = int(round(nx * src.get_width()))
            ay = int(round(ny * src.get_height()))
        except (TypeError, ValueError):
            pass
    dx, dy = 0, 0
    offset_px = meta.get("offset_px")
    if isinstance(offset_px, (list, tuple)) and len(offset_px) == 2:
        try:
            dx = int(round(float(offset_px[0])))
            dy = int(round(float(offset_px[1])))
        except (TypeError, ValueError):
            dx, dy = 0, 0
    ax = max(0, min(src.get_width(), ax))
    ay = max(0, min(src.get_height(), ay))
    return src, (ax, ay), (dx, dy)


def _procedural_building_sprite(b_type: str, level: int) -> pygame.Surface:
    w, h = TILE_W + 8, TILE_H + 16
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    fill, outline = _building_palette(b_type)
    body = pygame.Rect(6, 8, w - 12, h - 14)
    pygame.draw.rect(surf, fill, body, border_radius=4)
    pygame.draw.rect(surf, outline, body, 2, border_radius=4)
    lvl = max(1, min(level, 10))
    pygame.draw.rect(
        surf,
        (220, 200, 80),
        (body.centerx - 6, body.top - 6, 12, 8),
        border_radius=2,
    )
    font = pygame.font.Font(None, 12)
    txt = font.render(str(lvl), True, (20, 20, 20))
    surf.blit(txt, (body.right - txt.get_width() - 4, body.top + 2))
    return surf


@functools.lru_cache(maxsize=256)
def _load_building_meta_by_mtime(path_s: str, mtime_ns: int) -> dict:
    _ = mtime_ns
    path = Path(path_s)
    if not path.exists():
        return {}
    try:
        # utf-8-sig tolerates BOM that Windows tools may write.
        parsed = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _load_building_meta(folder: str) -> dict:
    path = _BUILDINGS_ROOT / folder / "asset_meta.json"
    if not path.exists():
        return {}
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return {}
    return _load_building_meta_by_mtime(str(path), mtime_ns)


def _building_level_candidates(folder: str, lvl: int) -> tuple[Path, ...]:
    return (
        _BUILDINGS_ROOT / folder / f"level_{lvl:02d}.png",
        _BUILDINGS_ROOT / folder / f"level_{lvl}.png",
        _BUILDINGS_ROOT / folder / "default.png",
    )


def _building_construction_candidates(folder: str, lvl: int) -> tuple[Path, ...]:
    return (
        _BUILDINGS_ROOT / folder / f"construction_{lvl}.png",
        _BUILDINGS_ROOT / folder / f"construction_{lvl:02d}.png",
        _BUILDINGS_ROOT / folder / "construction.png",
    )


def _meta_for_level(meta: dict, lvl: int) -> dict:
    out: dict = {}
    default = meta.get("default")
    if isinstance(default, dict):
        out.update(default)
    levels = meta.get("levels")
    if isinstance(levels, dict):
        lv = levels.get(str(lvl))
        if lv is None:
            lv = levels.get(f"{lvl:02d}")
        if isinstance(lv, dict):
            out.update(lv)
    return out


def _meta_for_variant_level(meta: dict, variant: str, lvl: int) -> dict:
    """Read meta for a specific visual variant (ready/construction), with legacy fallback."""
    payload = meta.get(variant)
    if isinstance(payload, dict):
        return _meta_for_level(payload, lvl)
    # Backward compatibility for legacy flat format.
    return _meta_for_level(meta, lvl)


def _apply_building_meta(src: pygame.Surface, meta: dict) -> tuple[pygame.Surface, tuple[int, int]]:
    scale_raw = meta.get("scale", 1.0)
    try:
        scale = float(scale_raw)
    except (TypeError, ValueError):
        scale = 1.0
    if scale <= 0:
        scale = 1.0

    if scale != 1.0:
        sw = max(1, int(round(src.get_width() * scale)))
        sh = max(1, int(round(src.get_height() * scale)))
        src = pygame.transform.smoothscale(src, (sw, sh))

    ax = src.get_width() // 2
    ay = src.get_height()

    anchor_norm = meta.get("anchor_norm")
    if isinstance(anchor_norm, (list, tuple)) and len(anchor_norm) == 2:
        try:
            nx = float(anchor_norm[0])
            ny = float(anchor_norm[1])
            ax = int(round(nx * src.get_width()))
            ay = int(round(ny * src.get_height()))
        except (TypeError, ValueError):
            pass
    else:
        anchor_px = meta.get("anchor_px")
        if isinstance(anchor_px, (list, tuple)) and len(anchor_px) == 2:
            try:
                px = float(anchor_px[0])
                py = float(anchor_px[1])
                ax = int(round(px * scale))
                ay = int(round(py * scale))
            except (TypeError, ValueError):
                pass

    ax = max(0, min(src.get_width(), ax))
    ay = max(0, min(src.get_height(), ay))
    return src, (ax, ay)


def _building_render_spec(b_type: str, level: int) -> tuple[pygame.Surface, tuple[int, int]]:
    """Return (surface, anchor_px) where anchor sits on footprint bottom-center."""
    folder = _building_folder_name(b_type)
    requested_level = int(level)
    is_field_empty_level = (
        b_type.upper().replace(" ", "_") == "FIELD" and requested_level == 0
    )
    lvl = 0 if is_field_empty_level else max(1, min(requested_level, 10))
    src: pygame.Surface | None = None
    for candidate in _building_level_candidates(folder, lvl):
        src = _load_png(str(candidate))
        if src is not None:
            break
    if src is None:
        src = _procedural_building_sprite(b_type, lvl)
    meta = _meta_for_variant_level(_load_building_meta(folder), "ready", lvl)
    return _apply_building_meta(src, meta)


def building_sprite(b_type: str, level: int) -> pygame.Surface:
    """Load building sprite from assets folder, fallback to procedural."""
    return _building_render_spec(b_type, level)[0]


def building_sprite_anchor(b_type: str, level: int) -> tuple[int, int]:
    """Return anchor pixel in building sprite (x,y)."""
    return _building_render_spec(b_type, level)[1]


def _procedural_building_construction_sprite(b_type: str, target_level: int) -> pygame.Surface:
    base = building_sprite(b_type, target_level).copy()
    base.set_alpha(180)
    w, h = base.get_size()
    scaffold = pygame.Color(136, 96, 56, 220)
    for x in range(4, w, 8):
        pygame.draw.line(base, scaffold, (x, 3), (x, h - 3), 2)
    for y in range(6, h, 10):
        pygame.draw.line(base, scaffold, (2, y), (w - 2, y), 2)
    pygame.draw.line(base, scaffold, (2, 3), (w - 2, h - 3), 2)
    pygame.draw.line(base, scaffold, (w - 2, 3), (2, h - 3), 2)
    return base


def _building_construction_render_spec(
    b_type: str, target_level: int
) -> tuple[pygame.Surface, tuple[int, int]]:
    """Load construction-state sprite + anchor, applying building asset meta transform."""
    folder = _building_folder_name(b_type)
    lvl = max(1, min(int(target_level), 10))
    src: pygame.Surface | None = None
    for candidate in _building_construction_candidates(folder, lvl):
        src = _load_png(str(candidate))
        if src is not None:
            break
    if src is None:
        src = _procedural_building_construction_sprite(b_type, lvl)
    meta = _meta_for_variant_level(_load_building_meta(folder), "construction", lvl)
    return _apply_building_meta(src, meta)


def building_sprite_construction(b_type: str, target_level: int) -> pygame.Surface:
    """Load construction-state sprite from disk, fallback to scaffolded procedural variant."""
    return _building_construction_render_spec(b_type, target_level)[0]


def building_sprite_construction_anchor(b_type: str, target_level: int) -> tuple[int, int]:
    """Return anchor pixel in construction-state building sprite (x,y)."""
    return _building_construction_render_spec(b_type, target_level)[1]


def _worker_color(w_type: str) -> tuple[int, int, int]:
    t = w_type.upper().replace(" ", "_")
    colors: dict[str, tuple[int, int, int]] = {
        "LUMBERJACK": (40, 140, 220),
        "STONECUTTER": (160, 160, 170),
        "MINER": (200, 90, 70),
        "FARMER": (230, 200, 60),
        "ANIMAL_HERDER": (176, 142, 92),
        "FORESTER": (88, 170, 96),
        "CARRIER": (170, 140, 92),
        "BUILDER": (186, 132, 96),
        "SAWYER": (200, 160, 80),
        "MILLER": (224, 210, 166),
        "BAKER": (232, 184, 132),
        "COOK": (200, 120, 88),
        "WATERMAN": (72, 148, 210),
    }
    return colors.get(t, (200, 200, 220))


def _procedural_worker_dot(w_type: str) -> pygame.Surface:
    size = 14
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, _worker_color(w_type), (size // 2, size // 2), size // 2 - 1)
    pygame.draw.circle(surf, (20, 20, 30), (size // 2, size // 2), size // 2 - 1, 1)
    return surf


def _procedural_worker_carry_dot(w_type: str) -> pygame.Surface:
    surf = _procedural_worker_dot(w_type).copy()
    w, h = surf.get_size()
    box = pygame.Rect(w // 2 - 4, h // 2 - 1, 8, 5)
    pygame.draw.rect(surf, (132, 92, 52), box, border_radius=1)
    pygame.draw.rect(surf, (28, 24, 18), box, width=1, border_radius=1)
    return surf


def _procedural_worker_carry_stone_dot(w_type: str) -> pygame.Surface:
    """Stonecutter-specific carrying fallback: visible gray stone payload."""
    surf = _procedural_worker_dot(w_type).copy()
    w, h = surf.get_size()
    cx = w // 2
    cy = h // 2
    pygame.draw.circle(surf, (164, 168, 176), (cx + 2, cy + 1), 3)
    pygame.draw.circle(surf, (84, 88, 98), (cx + 2, cy + 1), 3, 1)
    return surf


@functools.lru_cache(maxsize=128)
def _worker_dot_by_mtime(
    w_type: str,
    carrying: bool,
    default_mtime_ns: int,
    default_size: int,
    carrying_mtime_ns: int,
    carrying_size: int,
) -> pygame.Surface:
    _ = default_mtime_ns
    _ = default_size
    _ = carrying_mtime_ns
    _ = carrying_size
    t = w_type.upper().replace(" ", "_")
    folder = _WORKER_FOLDER.get(t, t.lower())
    name = "carrying.png" if carrying else "default.png"
    loaded = _load_png(str(_NPC_ROOT / folder / name))
    if loaded is not None:
        return loaded
    if carrying:
        if t == "STONECUTTER":
            return _procedural_worker_carry_stone_dot(w_type)
        return _procedural_worker_carry_dot(w_type)
    return _procedural_worker_dot(w_type)


def worker_dot(w_type: str, carrying: bool = False) -> pygame.Surface:
    """Load worker icon from assets folder, fallback to procedural."""
    t = w_type.upper().replace(" ", "_")
    folder = _WORKER_FOLDER.get(t, t.lower())
    default_path = _NPC_ROOT / folder / "default.png"
    carrying_path = _NPC_ROOT / folder / "carrying.png"
    default_mtime_ns = default_path.stat().st_mtime_ns if default_path.exists() else -1
    default_size = default_path.stat().st_size if default_path.exists() else -1
    carrying_mtime_ns = carrying_path.stat().st_mtime_ns if carrying_path.exists() else -1
    carrying_size = carrying_path.stat().st_size if carrying_path.exists() else -1
    return _worker_dot_by_mtime(
        w_type,
        carrying,
        default_mtime_ns,
        default_size,
        carrying_mtime_ns,
        carrying_size,
    )


def _hire_icon_fallback(w_type: str) -> pygame.Surface:
    size = 20
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    bg = pygame.Rect(1, 1, size - 2, size - 2)
    pygame.draw.rect(surf, (70, 86, 110), bg, border_radius=4)
    pygame.draw.rect(surf, (24, 30, 42), bg, width=1, border_radius=4)
    # Plus mark
    cx, cy = size // 2, size // 2
    pygame.draw.line(surf, (220, 232, 248), (cx - 4, cy), (cx + 4, cy), 2)
    pygame.draw.line(surf, (220, 232, 248), (cx, cy - 4), (cx, cy + 4), 2)
    return surf


@functools.lru_cache(maxsize=64)
def _load_fixed_icon(kind: str, worker_type: str, size: int) -> pygame.Surface:
    t = worker_type.upper().replace(" ", "_")
    folder = _WORKER_FOLDER.get(t, t.lower())
    if kind == "worker":
        path = _ICONS_ROOT / "workers" / f"{folder}.png"
        base = _load_png(str(path)) or _procedural_worker_dot(worker_type)
    else:
        path = _ICONS_ROOT / "hire" / f"{folder}.png"
        base = _load_png(str(path)) or _hire_icon_fallback(worker_type)
    sz = max(1, int(size))
    return pygame.transform.smoothscale(base, (sz, sz))


def worker_ui_icon(worker_type: str, size: int = 24) -> pygame.Surface:
    return _load_fixed_icon("worker", worker_type, size)


def hire_ui_icon(worker_type: str, size: int = 20) -> pygame.Surface:
    return _load_fixed_icon("hire", worker_type, size)


def _resource_colors(name: str) -> tuple[int, int, int]:
    key = name.lower()
    colors: dict[str, tuple[int, int, int]] = {
        "wheat": (230, 170, 80),
        "wood": (150, 100, 60),
        "stone": (170, 170, 180),
        "iron": (190, 120, 110),
        "boards": (210, 156, 102),
        "flour": (238, 228, 192),
        "bread": (194, 128, 72),
        "water": (70, 150, 220),
        "chicken": (214, 198, 154),
        "beef": (140, 52, 52),
        "hide": (120, 92, 68),
        "grapes": (112, 48, 140),
        "simple_meal": (210, 150, 95),
    }
    return colors.get(key, (160, 160, 200))


@functools.lru_cache(maxsize=16)
def resource_icon(name: str) -> pygame.Surface:
    size = 28
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = _resource_colors(name)
    pygame.draw.circle(surf, c, (size // 2, size // 2), size // 2 - 2)
    pygame.draw.circle(surf, (30, 30, 40), (size // 2, size // 2), size // 2 - 2, 2)
    return surf


def _procedural_population_icon(size: int = 24) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    pygame.draw.circle(surf, (218, 206, 120), (cx, cx - 4), max(3, size // 6))
    pygame.draw.circle(surf, (160, 148, 76), (cx, cx + 7), max(5, size // 4))
    pygame.draw.circle(surf, (34, 34, 40), (cx, cx - 4), max(3, size // 6), 1)
    pygame.draw.circle(surf, (34, 34, 40), (cx, cx + 7), max(5, size // 4), 1)
    return surf


@functools.lru_cache(maxsize=8)
def population_icon(size: int = 24) -> pygame.Surface:
    loaded = _load_png(str(_UI_ROOT / "population" / "default.png"))
    base = loaded if loaded is not None else _procedural_population_icon(max(1, int(size)))
    sz = max(1, int(size))
    if base.get_width() == sz and base.get_height() == sz:
        return base
    return pygame.transform.smoothscale(base, (sz, sz))


def clear_asset_caches() -> None:
    """Clear all in-memory asset caches (used by dev reload button)."""
    grass_tile.cache_clear()
    _load_png_by_mtime.cache_clear()
    _load_tree_meta.cache_clear()
    _load_stone_meta.cache_clear()
    _load_iron_meta.cache_clear()
    _load_gold_meta.cache_clear()
    _tree_render_spec.cache_clear()
    _stone_render_spec.cache_clear()
    _iron_render_spec.cache_clear()
    _gold_render_spec.cache_clear()
    _load_building_meta_by_mtime.cache_clear()
    _load_fixed_icon.cache_clear()
    _worker_dot_by_mtime.cache_clear()
    resource_icon.cache_clear()
    population_icon.cache_clear()
