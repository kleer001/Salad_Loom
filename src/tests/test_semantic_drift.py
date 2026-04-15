"""Tests for SemanticDriftNode."""
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

def make_sd(drift_rate=0.5, drift_distance=0.0, seed=42, target_pos="NN,NNS,JJ,VB"):
    n = Node.create_node(NodeType.SEMANTIC_DRIFT, "sd")
    n._parms["drift_rate"].set(drift_rate)
    n._parms["drift_distance"].set(drift_distance)
    n._parms["seed"].set(seed)
    n._parms["target_pos"].set(target_pos)
    n._parms["model_path"].set(MODEL_PATH)
    return n

def test_output_count_matches_input():
    src = make_src('["the tired surgeon stitched the wound", "a cat sat on the mat"]')
    sd = make_sd()
    sd.set_input(0, src)
    sd.cook()
    assert len(sd._output) == 2

def test_zero_drift_rate_no_change():
    src = make_src('["the cat sat on the mat"]')
    sd = make_sd(drift_rate=0.0, seed=0)
    sd.set_input(0, src)
    sd.cook()
    assert sd._output == ["the cat sat on the mat"]

def test_deterministic_with_seed():
    src1 = make_src('["the old surgeon crossed the river"]', "s1")
    sd1 = make_sd(drift_rate=0.5, seed=7)
    sd1.set_input(0, src1)
    sd1.cook()

    NodeEnvironment.get_instance().nodes.clear()
    src2 = make_src('["the old surgeon crossed the river"]', "s2")
    sd2 = make_sd(drift_rate=0.5, seed=7)
    sd2.set_input(0, src2)
    sd2.cook()

    assert sd1._output == sd2._output

def test_invalid_model_path_returns_error():
    src = make_src('["hello world"]')
    sd = Node.create_node(NodeType.SEMANTIC_DRIFT, "sd_bad")
    sd._parms["model_path"].set("/nonexistent/model.kv")
    sd._parms["drift_rate"].set(0.5)
    sd.set_input(0, src)
    sd.cook()
    assert any("error" in s.lower() for s in sd._output)
