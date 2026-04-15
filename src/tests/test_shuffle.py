"""Tests for ShuffleNode."""
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


def make_text_node(items):
    from core.text_node import TextNode
    import json
    node = Node.create_node(NodeType.TEXT, "text_src")
    node._parms["text_string"].set(str(items).replace("'", '"'))
    node._parms["pass_through"].set(False)
    return node


def make_shuffle(mode="items", seed=42):
    node = Node.create_node(NodeType.SHUFFLE, "shuffle")
    node._parms["mode"].set(mode)
    node._parms["seed"].set(seed)
    return node


def test_items_mode_preserves_all_items():
    src = make_text_node('["alpha", "beta", "gamma", "delta"]')
    sh = make_shuffle(mode="items", seed=99)
    sh.set_input(0, src)
    sh.cook()
    result = sh._output
    assert sorted(result) == ["alpha", "beta", "delta", "gamma"]


def test_items_mode_is_deterministic_with_seed():
    src = make_text_node('["a", "b", "c", "d", "e"]')
    sh1 = make_shuffle(mode="items", seed=7)
    sh1.set_input(0, src)
    sh1.cook()

    NodeEnvironment.get_instance().nodes.clear()
    src2 = Node.create_node(NodeType.TEXT, "text_src2")
    src2._parms["text_string"].set('["a", "b", "c", "d", "e"]')
    src2._parms["pass_through"].set(False)
    sh2 = Node.create_node(NodeType.SHUFFLE, "shuffle2")
    sh2._parms["mode"].set("items")
    sh2._parms["seed"].set(7)
    sh2.set_input(0, src2)
    sh2.cook()

    assert sh1._output == sh2._output


def test_words_mode_shuffles_within_strings():
    src = make_text_node('["hello world foo bar"]')
    sh = make_shuffle(mode="words", seed=42)
    sh.set_input(0, src)
    sh.cook()
    result = sh._output
    assert len(result) == 1
    assert sorted(result[0].split()) == ["bar", "foo", "hello", "world"]


def test_sentences_mode_shuffles_sentences():
    src = make_text_node('["First sentence. Second sentence. Third sentence."]')
    sh = make_shuffle(mode="sentences", seed=1)
    sh.set_input(0, src)
    sh.cook()
    result = sh._output
    assert len(result) == 1
    # All three sentences must still be present
    for s in ["First sentence.", "Second sentence.", "Third sentence."]:
        assert s in result[0]


def test_empty_input_returns_empty():
    src = make_text_node('[]')
    sh = make_shuffle(mode="items", seed=0)
    sh.set_input(0, src)
    sh.cook()
    assert sh._output == [] or sh._output == [""]
