"""Failing domain tests for tree species and growth ticks (T149)."""

from __future__ import annotations

from game.trees import Tree, TreeStage


def test_tree_supports_exactly_three_species_ids() -> None:
    allowed = {0, 1, 2}
    for species in allowed:
        tree = Tree(stage=TreeStage.SAPLING, species=species)
        assert tree.species == species

    for invalid in (-1, 3):
        try:
            Tree(stage=TreeStage.SAPLING, species=invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for invalid species")


def test_tree_growth_advances_every_30_seconds() -> None:
    tree = Tree(stage=TreeStage.SAPLING, species=0, next_growth_at_ms=30_000)
    assert tree.stage == TreeStage.SAPLING

    tree.update_growth(now_ms=29_999)
    assert tree.stage == TreeStage.SAPLING

    tree.update_growth(now_ms=30_000)
    assert tree.stage == TreeStage.YOUNG
    assert tree.next_growth_at_ms == 60_000

    tree.update_growth(now_ms=90_000)
    assert tree.stage == TreeStage.ADULT
    assert tree.next_growth_at_ms == 120_000


def test_stage_progression_is_species_independent() -> None:
    tree_a = Tree(stage=TreeStage.SAPLING, species=0, next_growth_at_ms=30_000)
    tree_b = Tree(stage=TreeStage.SAPLING, species=2, next_growth_at_ms=30_000)

    for now in (30_000, 60_000, 90_000):
        tree_a.update_growth(now_ms=now)
        tree_b.update_growth(now_ms=now)
        assert tree_a.stage == tree_b.stage
