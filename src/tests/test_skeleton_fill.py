"""Tests for SkeletonFillNode."""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from core.base_classes import NodeEnvironment
from core.node import Node
from core.enums import NodeType


@pytest.fixture(autouse=True)
def clear_env():
    NodeEnvironment.get_instance().nodes.clear()
    yield
    NodeEnvironment.get_instance().nodes.clear()


def make_src(text_str, name="src"):
    node = Node.create_node(NodeType.TEXT, name)
    node._parms["text_string"].set(text_str)
    node._parms["pass_through"].set(False)
    return node


def make_fill(mode="random", seed=42, allow_repeats=True):
    node = Node.create_node(NodeType.SKELETON_FILL, "fill")
    node._parms["mode"].set(mode)
    node._parms["seed"].set(seed)
    node._parms["allow_repeats"].set(allow_repeats)
    return node


def test_all_slots_filled():
    skeleton_src = make_src('["The [JJ] [NN] [VBD] the [NN]"]', "skel")
    pool_src = make_src('["funny/JJ", "cat/NN", "dog/NN", "chased/VBD"]', "pool")
    fill = make_fill()
    fill.set_input(0, skeleton_src)
    fill.set_input(1, pool_src)
    fill.cook()
    result = fill._output[0]
    # No [TAG] slots should remain
    assert not re.search(r'\[[A-Z$]+\]', result)


def test_pos_matching():
    skeleton_src = make_src('["The [NN] ran"]', "skel")
    pool_src = make_src('["mountain/NN", "run/VB", "blue/JJ"]', "pool")
    fill = make_fill(seed=1)
    fill.set_input(0, skeleton_src)
    fill.set_input(1, pool_src)
    fill.cook()
    result = fill._output[0]
    assert "mountain" in result
    assert "run" not in result
    assert "blue" not in result


def test_no_match_tag_leaves_slot():
    skeleton_src = make_src('["The [ZZZZ] ran"]', "skel")
    pool_src = make_src('["cat/NN", "dog/NN"]', "pool")
    fill = make_fill()
    fill.set_input(0, skeleton_src)
    fill.set_input(1, pool_src)
    fill.cook()
    result = fill._output[0]
    # Unknown tag — slot should remain
    assert "[ZZZZ]" in result


def test_sequential_mode_cycles():
    skeleton_src = make_src('["[NN] [NN] [NN]"]', "skel")
    pool_src = make_src('["alpha/NN", "beta/NN"]', "pool")
    fill = make_fill(mode="sequential")
    fill.set_input(0, skeleton_src)
    fill.set_input(1, pool_src)
    fill.cook()
    result = fill._output[0]
    words = result.split()
    assert words[0] == "alpha"
    assert words[1] == "beta"
    assert words[2] == "alpha"  # cycles


def test_output_count_matches_skeleton_count():
    skeleton_src = make_src('["[NN] ran", "[JJ] cat", "[VB] now"]', "skel")
    pool_src = make_src('["dog/NN", "fast/JJ", "jump/VB"]', "pool")
    fill = make_fill()
    fill.set_input(0, skeleton_src)
    fill.set_input(1, pool_src)
    fill.cook()
    assert len(fill._output) == 3
