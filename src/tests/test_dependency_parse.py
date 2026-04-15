"""Tests for DependencyParseNode."""
import sys, os, re
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

def make_dp(output_format="skeleton", preserve="det,prep,aux,cc,punct,mark"):
    n = Node.create_node(NodeType.DEPENDENCY_PARSE, "dp")
    n._parms["output_format"].set(output_format)
    n._parms["preserve"].set(preserve)
    return n

def test_skeleton_mode_produces_slots():
    src = make_src('["The tired surgeon stitched the wound"]')
    dp = make_dp(output_format="skeleton")
    dp.set_input(0, src)
    dp.cook()
    result = dp._output[0]
    # Should have at least one [dep] slot
    assert re.search(r"\[[a-z]+\]", result)

def test_skeleton_preserves_det():
    src = make_src('["The dog runs"]')
    dp = make_dp(output_format="skeleton", preserve="det")
    dp.set_input(0, src)
    dp.cook()
    result = dp._output[0]
    assert "The" in result

def test_flat_mode_has_slash_format():
    src = make_src('["cats sleep"]')
    dp = make_dp(output_format="flat")
    dp.set_input(0, src)
    dp.cook()
    result = dp._output[0]
    # flat format: word/POS/DEP/head
    assert "/" in result

def test_output_count_matches_input():
    src = make_src('["first sentence", "second sentence"]')
    dp = make_dp()
    dp.set_input(0, src)
    dp.cook()
    assert len(dp._output) == 2
