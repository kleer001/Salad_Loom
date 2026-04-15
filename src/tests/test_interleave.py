"""Tests for InterleaveNode."""
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


def make_list_src(items_str, name="src"):
    node = Node.create_node(NodeType.TEXT, name)
    node._parms["text_string"].set(items_str)
    node._parms["pass_through"].set(False)
    return node


def make_interleave(mode="items", ratio="1:1"):
    node = Node.create_node(NodeType.INTERLEAVE, "interleave")
    node._parms["mode"].set(mode)
    node._parms["ratio"].set(ratio)
    return node


def test_items_mode_alternates():
    a = make_list_src('["a1", "a2", "a3"]', "src_a")
    b = make_list_src('["b1", "b2", "b3"]', "src_b")
    il = make_interleave(mode="items", ratio="1:1")
    il.set_input(0, a)
    il.set_input(1, b)
    il.cook()
    result = il._output
    # Should interleave: a1, b1, a2, b2, a3, b3
    assert result[0] == "a1"
    assert result[1] == "b1"
    assert result[2] == "a2"
    assert result[3] == "b2"


def test_ratio_mode_2_1():
    a = make_list_src('["a1", "a2", "a3", "a4"]', "src_a")
    b = make_list_src('["b1", "b2"]', "src_b")
    il = make_interleave(mode="items", ratio="2:1")
    il.set_input(0, a)
    il.set_input(1, b)
    il.cook()
    result = il._output
    # a1, a2, b1, a3, a4, b2, ...
    assert result[0] == "a1"
    assert result[1] == "a2"
    assert result[2] == "b1"


def test_unequal_lengths_cycles_shorter():
    a = make_list_src('["x", "y"]', "src_a")
    b = make_list_src('["1", "2", "3", "4"]', "src_b")
    il = make_interleave(mode="items", ratio="1:1")
    il.set_input(0, a)
    il.set_input(1, b)
    il.cook()
    result = il._output
    assert len(result) > 0
    assert "x" in result or "y" in result
    assert "1" in result


def test_words_mode_interleaves_within_strings():
    a = make_list_src('["hello world"]', "src_a")
    b = make_list_src('["foo bar"]', "src_b")
    il = make_interleave(mode="words", ratio="1:1")
    il.set_input(0, a)
    il.set_input(1, b)
    il.cook()
    result = il._output
    assert len(result) == 1
    words = result[0].split()
    assert "hello" in words
    assert "foo" in words
