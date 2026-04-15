"""Tests for ConjugationFixerNode."""
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

def make_cf(fix_articles=True, fix_cap=True, fix_verbs=False):
    n = Node.create_node(NodeType.CONJUGATION_FIXER, "cf")
    n._parms["fix_articles"].set(fix_articles)
    n._parms["fix_capitalization"].set(fix_cap)
    n._parms["fix_verbs"].set(fix_verbs)
    return n

def test_a_to_an_before_vowel():
    src = make_src('["a apple"]')
    cf = make_cf(fix_articles=True, fix_cap=False, fix_verbs=False)
    cf.set_input(0, src)
    cf.cook()
    assert cf._output[0] == "an apple"

def test_an_to_a_before_consonant():
    src = make_src('["an dog"]')
    cf = make_cf(fix_articles=True, fix_cap=False, fix_verbs=False)
    cf.set_input(0, src)
    cf.cook()
    assert cf._output[0] == "a dog"

def test_capitalize_sentence_start():
    src = make_src('["hello world. goodbye moon."]')
    cf = make_cf(fix_articles=False, fix_cap=True, fix_verbs=False)
    cf.set_input(0, src)
    cf.cook()
    result = cf._output[0]
    assert result[0].isupper()
    assert "Goodbye" in result

def test_output_count_matches_input():
    src = make_src('["one", "two", "three"]')
    cf = make_cf()
    cf.set_input(0, src)
    cf.cook()
    assert len(cf._output) == 3
