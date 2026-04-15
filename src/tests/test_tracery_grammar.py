"""Tests for TraceryGrammarNode."""
import sys, os, json
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

GRAMMAR = {
    "origin": ["The #adj# #creature# #action# the #adj# #object#."],
    "adj": ["decaffeinated", "logarithmic", "anxious"],
    "creature": ["hermit crab", "penguin", "turnip"],
    "action": ["interrogated", "defenestrated", "baptized"],
    "object": ["spreadsheet", "glacier", "sandwich"]
}

def make_grammar_src(grammar_dict, name="src"):
    n = Node.create_node(NodeType.TEXT, name)
    n._parms["text_string"].set(json.dumps(grammar_dict))
    n._parms["pass_through"].set(False)
    return n

def make_tg(start="origin", count=5, seed=42):
    n = Node.create_node(NodeType.TRACERY_GRAMMAR, "tg")
    n._parms["start_symbol"].set(start)
    n._parms["count"].set(count)
    n._parms["seed"].set(seed)
    return n

def test_output_count():
    src = make_grammar_src(GRAMMAR)
    tg = make_tg(count=7)
    tg.set_input(0, src)
    tg.cook()
    assert len(tg._output) == 7

def test_no_unresolved_symbols():
    src = make_grammar_src(GRAMMAR)
    tg = make_tg(count=10, seed=1)
    tg.set_input(0, src)
    tg.cook()
    for s in tg._output:
        assert "#" not in s, f"Unresolved symbol in: {s}"

def test_deterministic_with_seed():
    src1 = make_grammar_src(GRAMMAR, "src1")
    tg1 = make_tg(seed=99)
    tg1.set_input(0, src1)
    tg1.cook()

    NodeEnvironment.get_instance().nodes.clear()
    src2 = make_grammar_src(GRAMMAR, "src2")
    tg2 = make_tg(seed=99)
    tg2.set_input(0, src2)
    tg2.cook()

    assert tg1._output == tg2._output

def test_capitalize_modifier():
    grammar = {"origin": ["#word.capitalize#"], "word": ["hello"]}
    src = make_grammar_src(grammar)
    tg = make_tg(count=1, seed=0)
    tg.set_input(0, src)
    tg.cook()
    assert tg._output[0] == "Hello"

def test_a_modifier():
    grammar = {"origin": ["#item.a#"], "item": ["apple"]}
    src = make_grammar_src(grammar)
    tg = make_tg(count=1, seed=0)
    tg.set_input(0, src)
    tg.cook()
    assert tg._output[0] == "an apple"

def test_s_modifier():
    grammar = {"origin": ["#animal.s#"], "animal": ["cat"]}
    src = make_grammar_src(grammar)
    tg = make_tg(count=1, seed=0)
    tg.set_input(0, src)
    tg.cook()
    assert tg._output[0] == "cats"

def test_invalid_json_returns_error():
    n = Node.create_node(NodeType.TEXT, "bad_src")
    n._parms["text_string"].set("not json at all")
    n._parms["pass_through"].set(False)
    tg = make_tg()
    tg.set_input(0, n)
    tg.cook()
    assert any("error" in s.lower() for s in tg._output)

def test_missing_start_symbol_returns_error():
    src = make_grammar_src(GRAMMAR)
    tg = make_tg(start="nonexistent", count=1)
    tg.set_input(0, src)
    tg.cook()
    assert any("error" in s.lower() for s in tg._output)
