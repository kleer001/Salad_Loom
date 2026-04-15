"""Tests for NPlusSevenNode."""
import sys
import os
import tempfile

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


@pytest.fixture()
def small_dict(tmp_path):
    """A minimal sorted dictionary for predictable substitution testing."""
    words = ["apple", "banana", "cherry", "date", "elderberry",
             "fig", "grape", "honeydew", "kiwi", "lemon",
             "mango", "nectarine", "orange", "peach", "plum"]
    p = tmp_path / "test_dict.txt"
    p.write_text("\n".join(words))
    return str(p)


def make_src(text_str, name="src"):
    node = Node.create_node(NodeType.TEXT, name)
    node._parms["text_string"].set(text_str)
    node._parms["pass_through"].set(False)
    return node


def make_n7(offset=7, target_pos="nouns", dict_path=""):
    node = Node.create_node(NodeType.N_PLUS_7, "n_plus_7")
    node._parms["offset"].set(offset)
    node._parms["target_pos"].set(target_pos)
    node._parms["dictionary"].set(dict_path)
    return node


def test_known_substitution_with_small_dict(small_dict):
    # "apple" is index 0, offset 7 → "honeydew"
    src = make_src('["apple"]')
    n7 = make_n7(offset=7, target_pos="all", dict_path=small_dict)
    n7.set_input(0, src)
    n7.cook()
    result = n7._output
    assert len(result) == 1
    # "apple" should be replaced by a word 7 positions later
    assert "apple" not in result[0]


def test_pos_filtering_nouns_only(small_dict):
    # "runs" is a verb — should NOT be replaced in nouns mode
    src = make_src('["The dog runs fast"]')
    n7 = make_n7(offset=1, target_pos="nouns", dict_path=small_dict)
    n7.set_input(0, src)
    n7.cook()
    result = n7._output
    assert len(result) == 1
    # "runs" should remain (it's a verb, not a noun)
    assert "runs" in result[0]


def test_output_count_matches_input(small_dict):
    src = make_src('["first sentence", "second sentence", "third sentence"]')
    n7 = make_n7(offset=3, target_pos="nouns", dict_path=small_dict)
    n7.set_input(0, src)
    n7.cook()
    assert len(n7._output) == 3


def test_missing_dictionary_returns_error():
    src = make_src('["hello world"]')
    n7 = make_n7(offset=7, target_pos="nouns", dict_path="/nonexistent/path.txt")
    n7.set_input(0, src)
    n7.cook()
    assert any("error" in s.lower() for s in n7._output)
