"""Tests for MarkovGenerateNode."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import markovify
from core.base_classes import NodeEnvironment
from core.node import Node
from core.enums import NodeType


@pytest.fixture(autouse=True)
def clear_env():
    NodeEnvironment.get_instance().nodes.clear()
    yield
    NodeEnvironment.get_instance().nodes.clear()


# Large enough corpus that markovify can generate sentences
CORPUS = [
    "The quick brown fox jumps over the lazy dog.",
    "A rolling stone gathers no moss over time.",
    "The cat sat on the mat near the door.",
    "All that glitters is not gold in the end.",
    "Better late than never when you are ready.",
    "Every cloud has a silver lining somewhere above.",
    "Fortune favours the brave and the bold alike.",
    "Haste makes waste when you rush without thinking.",
    "Ignorance is bliss until reality catches up.",
    "Knowledge is power when properly applied daily.",
] * 3  # repeat so markovify has enough transitions


def make_model_json():
    """Build a markovify model JSON directly without going through nodes."""
    corpus = " ".join(CORPUS)
    model = markovify.Text(corpus, state_size=2, retain_original=False)
    return model.to_json()


def make_json_src(json_str, name="json_src"):
    node = Node.create_node(NodeType.TEXT, name)
    escaped = json_str.replace('"', '\\"')
    node._parms["text_string"].set(f'["{escaped}"]')
    node._parms["pass_through"].set(False)
    return node


def make_gen(count=5, max_chars=280, tries=100, seed=-1):
    node = Node.create_node(NodeType.MARKOV_GENERATE, "gen")
    node._parms["count"].set(count)
    node._parms["max_chars"].set(max_chars)
    node._parms["tries"].set(tries)
    node._parms["seed"].set(seed)
    return node


def test_output_count():
    model_json = make_model_json()
    src = make_json_src(model_json)
    gen = make_gen(count=5)
    gen.set_input(0, src)
    gen.cook()
    # May generate fewer if tries exhausted, but should produce some
    assert len(gen._output) >= 1


def test_deterministic_with_seed():
    model_json = make_model_json()

    src1 = make_json_src(model_json, "src1")
    gen1 = make_gen(count=3, seed=42)
    gen1.set_input(0, src1)
    gen1.cook()
    result1 = gen1._output[:]

    NodeEnvironment.get_instance().nodes.clear()

    src2 = make_json_src(model_json, "src2")
    gen2 = make_gen(count=3, seed=42)
    gen2.set_input(0, src2)
    gen2.cook()
    result2 = gen2._output[:]

    assert result1 == result2


def test_max_chars_respected():
    model_json = make_model_json()
    src = make_json_src(model_json)
    gen = make_gen(count=10, max_chars=50)
    gen.set_input(0, src)
    gen.cook()
    for sentence in gen._output:
        if not sentence.startswith("["):  # skip error strings
            assert len(sentence) <= 50


def test_invalid_json_returns_error():
    src = Node.create_node(NodeType.TEXT, "bad_src")
    src._parms["text_string"].set('["not valid json at all"]')
    src._parms["pass_through"].set(False)
    gen = make_gen(count=3)
    gen.set_input(0, src)
    gen.cook()
    assert any("error" in s.lower() for s in gen._output)
