"""Tests for FoldInNode."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from core.base_classes import NodeEnvironment
from core.node import Node
from core.enums import NodeType

@pytest.fixture(autouse=True)
def clear_env():
    NodeEnvironment.get_instance().nodes.clear()
    yield
    NodeEnvironment.get_instance().nodes.clear()

def make_src(text, name="src"):
    n = Node.create_node(NodeType.TEXT, name)
    n._parms["text_string"].set(text)
    n._parms["pass_through"].set(False)
    return n

def make_fold(split_point=0.5, mode="characters"):
    n = Node.create_node(NodeType.FOLD_IN, "fold")
    n._parms["split_point"].set(split_point)
    n._parms["mode"].set(mode)
    return n

def test_output_count_matches_longer_input():
    a = make_src('["line one", "line two", "line three"]', "a")
    b = make_src('["alpha", "beta"]', "b")
    f = make_fold()
    f.set_input(0, a)
    f.set_input(1, b)
    f.cook()
    assert len(f._output) == 3

def test_characters_mode_combines_halves():
    a = make_src('["abcdefgh"]', "a")
    b = make_src('["12345678"]', "b")
    f = make_fold(split_point=0.5, mode="characters")
    f.set_input(0, a)
    f.set_input(1, b)
    f.cook()
    result = f._output[0]
    # Left half of a (abcd) + right half of b (5678)
    assert "abcd" in result
    assert "5678" in result

def test_words_mode():
    a = make_src('["the surgeon stitched the wound"]', "a")
    b = make_src('["the glacier released ancient sediment"]', "b")
    f = make_fold(split_point=0.5, mode="words")
    f.set_input(0, a)
    f.set_input(1, b)
    f.cook()
    result = f._output[0]
    words = result.split()
    # Should contain words from both inputs
    assert any(w in ["the", "surgeon", "stitched"] for w in words)
    assert any(w in ["ancient", "sediment"] for w in words)

def test_empty_string_input_a_produces_output():
    a = make_src('[]', "a")
    b = make_src('["hello world"]', "b")
    f = make_fold()
    f.set_input(0, a)
    f.set_input(1, b)
    f.cook()
    assert len(f._output) == 1
