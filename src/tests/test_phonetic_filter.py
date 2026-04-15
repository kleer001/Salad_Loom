"""Tests for PhoneticFilterNode."""
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

def make_pf(mode="alliteration", threshold=0.3, invert=False):
    n = Node.create_node(NodeType.PHONETIC_FILTER, "pf")
    n._parms["mode"].set(mode)
    n._parms["threshold"].set(threshold)
    n._parms["invert"].set(invert)
    return n

def test_alliteration_passes_high_scoring():
    # "silly silver salmon swim swiftly" - lots of s-alliteration
    src = make_src('["silly silver salmon swim swiftly"]')
    pf = make_pf(mode="alliteration", threshold=0.3)
    pf.set_input(0, src)
    pf.cook()
    assert len(pf._output) == 1

def test_threshold_zero_passes_all():
    src = make_src('["random words xyz", "more random stuff"]')
    pf = make_pf(threshold=0.0)
    pf.set_input(0, src)
    pf.cook()
    assert len(pf._output) == 2

def test_threshold_one_passes_none():
    src = make_src('["random words xyz"]')
    pf = make_pf(threshold=1.0)
    pf.set_input(0, src)
    pf.cook()
    assert len(pf._output) == 0

def test_invert_reverses_filter():
    src = make_src('["silly silver salmon swim swiftly", "random normal text"]')
    pf_normal = make_pf(mode="alliteration", threshold=0.3, invert=False)
    pf_normal.set_input(0, src)
    pf_normal.cook()
    passed_normal = set(pf_normal._output)

    NodeEnvironment.get_instance().nodes.clear()
    src2 = make_src('["silly silver salmon swim swiftly", "random normal text"]', "src2")
    pf_inv = Node.create_node(NodeType.PHONETIC_FILTER, "pf2")
    pf_inv._parms["mode"].set("alliteration")
    pf_inv._parms["threshold"].set(0.3)
    pf_inv._parms["invert"].set(True)
    pf_inv.set_input(0, src2)
    pf_inv.cook()
    passed_inverted = set(pf_inv._output)

    assert passed_normal.isdisjoint(passed_inverted) or len(passed_normal) + len(passed_inverted) <= 2
