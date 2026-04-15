"""Tests for RegexReplaceNode."""
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

def make_rr(pattern="", replacement="", count=0, flags=""):
    n = Node.create_node(NodeType.REGEX_REPLACE, "rr")
    n._parms["pattern"].set(pattern)
    n._parms["replacement"].set(replacement)
    n._parms["count"].set(count)
    n._parms["flags"].set(flags)
    return n

def test_basic_substitution():
    src = make_src('["hello world"]')
    rr = make_rr(pattern="world", replacement="salad")
    rr.set_input(0, src)
    rr.cook()
    assert rr._output == ["hello salad"]

def test_deletion():
    src = make_src('["hello world"]')
    rr = make_rr(pattern=r"\s+world", replacement="")
    rr.set_input(0, src)
    rr.cook()
    assert rr._output == ["hello"]

def test_count_limits_replacements():
    src = make_src('["aaa"]')
    rr = make_rr(pattern="a", replacement="b", count=2)
    rr.set_input(0, src)
    rr.cook()
    assert rr._output == ["bba"]

def test_ignorecase_flag():
    src = make_src('["Hello WORLD"]')
    rr = make_rr(pattern="hello", replacement="bye", flags="ignorecase")
    rr.set_input(0, src)
    rr.cook()
    assert rr._output == ["bye WORLD"]

def test_bad_pattern_returns_error():
    src = make_src('["test"]')
    rr = make_rr(pattern="[unclosed")
    rr.set_input(0, src)
    rr.cook()
    assert any("error" in s.lower() for s in rr._output)

def test_empty_pattern_passthrough():
    src = make_src('["unchanged"]')
    rr = make_rr(pattern="")
    rr.set_input(0, src)
    rr.cook()
    assert rr._output == ["unchanged"]

def test_backreference():
    src = make_src('["2026-04-15"]')
    rr = make_rr(pattern=r"(\d{4})-(\d{2})-(\d{2})", replacement=r"\3/\2/\1")
    rr.set_input(0, src)
    rr.cook()
    assert rr._output == ["15/04/2026"]
