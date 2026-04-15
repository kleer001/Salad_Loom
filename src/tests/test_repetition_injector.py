"""Tests for RepetitionInjectorNode."""
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

def make_ri(mode="word", density=1.0, max_repeats=2, seed=42):
    n = Node.create_node(NodeType.REPETITION_INJECTOR, "ri")
    n._parms["mode"].set(mode)
    n._parms["density"].set(density)
    n._parms["max_repeats"].set(max_repeats)
    n._parms["seed"].set(seed)
    return n

def test_word_mode_increases_length():
    src = make_src('["the old man crossed the street"]')
    ri = make_ri(mode="word", density=1.0, max_repeats=1, seed=0)
    ri.set_input(0, src)
    ri.cook()
    original_words = len("the old man crossed the street".split())
    result_words = len(ri._output[0].split())
    assert result_words > original_words

def test_density_zero_no_change():
    src = make_src('["hello world"]')
    ri = make_ri(mode="word", density=0.0, max_repeats=3, seed=0)
    ri.set_input(0, src)
    ri.cook()
    assert ri._output == ["hello world"]

def test_deterministic_with_seed():
    src1 = make_src('["cats and dogs"]', "src1")
    ri1 = make_ri(seed=7)
    ri1.set_input(0, src1)
    ri1.cook()

    NodeEnvironment.get_instance().nodes.clear()
    src2 = make_src('["cats and dogs"]', "src2")
    ri2 = make_ri(seed=7)
    ri2.set_input(0, src2)
    ri2.cook()

    assert ri1._output == ri2._output

def test_sentence_mode():
    src = make_src('["First sentence. Second sentence."]')
    ri = make_ri(mode="sentence", density=1.0, max_repeats=1, seed=0)
    ri.set_input(0, src)
    ri.cook()
    result = ri._output[0]
    assert len(result) > len("First sentence. Second sentence.")

def test_output_count_matches_input():
    src = make_src('["one", "two", "three"]')
    ri = make_ri()
    ri.set_input(0, src)
    ri.cook()
    assert len(ri._output) == 3
