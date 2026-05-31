"""Bundled UI font helper tests (T443)."""

from __future__ import annotations

from pathlib import Path

from game.ui.fonts import ui_font

_FONT_NONE_ALLOWLIST = (
    Path("src/game/dev_asset_reload.py"),
    Path("src/game/ui/fonts.py"),
)


def test_ui_font_renders_cyrillic_with_nonzero_width() -> None:
    surface = ui_font(22).render("Дерево", True, (255, 255, 255))
    assert surface.get_width() > 0


def test_ui_modules_do_not_use_font_none_literal() -> None:
    project_root = Path(__file__).resolve().parents[1]
    scan_roots = [
        project_root / "src" / "game" / "ui",
        project_root / "src" / "game" / "render.py",
        project_root / "src" / "game" / "assets.py",
    ]
    offenders: list[str] = []
    for root in scan_roots:
        paths = [root] if root.is_file() else sorted(root.rglob("*.py"))
        for path in paths:
            rel = path.relative_to(project_root)
            if rel in _FONT_NONE_ALLOWLIST:
                continue
            text = path.read_text(encoding="utf-8")
            if "Font(None" in text or "SysFont(None" in text:
                offenders.append(str(rel))
    assert offenders == []
