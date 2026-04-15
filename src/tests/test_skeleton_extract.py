"""Tests for SkeletonExtractNode."""
import sys
import os

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


def make_extract(preserve="DT,IN,CC,TO,PRP,MD", slot_format="[{tag}]"):
    node = Node.create_node(NodeType.SKELETON_EXTRACT, "extract")
    node._parms["preserve"].set(preserve)
    node._parms["slot_format"].set(slot_format)
    return node


def test_known_sentence_produces_expected_skeleton():
    src = make_src('["The old surgeon carefully stitched the wound"]')
    ex = make_extract()
    ex.set_input(0, src)
    ex.cook()
    result = ex._output
    assert len(result) == 1
    skeleton = result[0]
    # "The" (DT) and "the" (DT) should be preserved
    assert "The" in skeleton
    assert "the" in skeleton
    # Content words should be replaced with [TAG] slots
    assert "[" in skeleton and "]" in skeleton
    # Original content words should be gone
    for word in ["old", "surgeon", "carefully", "stitched", "wound"]:
        assert word not in skeleton


def test_custom_slot_format():
    src = make_src('["The big dog ran fast"]')
    ex = make_extract(slot_format="__{tag}__")
    ex.set_input(0, src)
    ex.cook()
    result = ex._output[0]
    assert "__" in result
    assert "[" not in result


def test_output_count_matches_input():
    src = make_src('["First sentence", "Second sentence", "Third sentence"]')
    ex = make_extract()
    ex.set_input(0, src)
    ex.cook()
    assert len(ex._output) == 3


def test_punctuation_preserved():
    src = make_src('["Hello, world!"]')
    ex = make_extract()
    ex.set_input(0, src)
    ex.cook()
    result = ex._output[0]
    assert "," in result or "!" in result
