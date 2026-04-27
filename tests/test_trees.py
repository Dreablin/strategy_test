"""Failing model tests for Phase 10 tree entities (T63)."""

from game.trees import Tree, TreeStage


def test_tree_stage_enum_order_is_deterministic() -> None:
    assert TreeStage.SAPLING.value < TreeStage.YOUNG.value
    assert TreeStage.YOUNG.value < TreeStage.MATURE.value
    assert TreeStage.MATURE.value < TreeStage.ADULT.value


def test_tree_defaults_alive_with_stage() -> None:
    tree = Tree(stage=TreeStage.SAPLING)
    assert tree.stage is TreeStage.SAPLING
    assert tree.alive is True


def test_tree_stage_index_matches_enum_order() -> None:
    assert Tree(TreeStage.SAPLING).stage_index < Tree(TreeStage.YOUNG).stage_index
    assert Tree(TreeStage.YOUNG).stage_index < Tree(TreeStage.MATURE).stage_index
    assert Tree(TreeStage.MATURE).stage_index < Tree(TreeStage.ADULT).stage_index


def test_cut_down_marks_tree_dead_and_non_blocking_semantics() -> None:
    tree = Tree(stage=TreeStage.ADULT)
    assert tree.alive is True
    tree.cut_down()
    assert tree.alive is False
