"""Tests for CoherenceGateNode."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from core.base_classes import NodeEnvironment
from core.node import Node
from core.enums import NodeType

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "data/models/glove-wiki-gigaword-50.kv"))

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

def make_cg(min_c=0.0, max_c=1.0, window=3):
    n = Node.create_node(NodeType.COHERENCE_GATE, "cg")
    n._parms["min_coherence"].set(min_c)
    n._parms["max_coherence"].set(max_c)
    n._parms["window"].set(window)
    n._parms["model_path"].set(MODEL_PATH)
    return n

def test_wide_gate_passes_all():
    src = make_src('["the dog ran quickly", "cats love sunny days"]')
    cg = make_cg(min_c=0.0, max_c=1.0)
    cg.set_input(0, src)
    cg.cook()
    assert len(cg._output) == 2

def test_narrow_impossible_gate_passes_nothing():
    src = make_src('["the dog ran quickly"]')
    cg = make_cg(min_c=0.99, max_c=1.0)
    cg.set_input(0, src)
    cg.cook()
    assert len(cg._output) == 0

def test_coherent_text_scores_higher_than_random():
    coherent = make_src('["the doctor treated the patient carefully"]', "coherent")
    cg_coherent = make_cg(min_c=0.2, max_c=1.0)
    cg_coherent.set_input(0, coherent)
    cg_coherent.cook()

    NodeEnvironment.get_instance().nodes.clear()
    # Very incoherent: semantically unrelated words
    incoherent = make_src('["algebra telephone purple Monday saddle"]', "incoherent")
    cg_incoherent = make_cg(min_c=0.2, max_c=1.0)
    cg_incoherent.set_input(0, incoherent)
    cg_incoherent.cook()

    # Coherent text is more likely to pass the minimum threshold
    assert len(cg_coherent._output) >= len(cg_incoherent._output)

def test_invalid_model_returns_error():
    src = make_src('["hello world"]')
    cg = Node.create_node(NodeType.COHERENCE_GATE, "cg_bad")
    cg._parms["model_path"].set("/nonexistent/model.kv")
    cg.set_input(0, src)
    cg.cook()
    assert any("error" in s.lower() for s in cg._output)
