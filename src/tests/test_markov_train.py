"""Tests for MarkovTrainNode."""
import sys
import os
import json

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


CORPUS = [
    "The cat sat on the mat.",
    "The dog lay on the rug.",
    "A fish swam in the pond.",
    "The bird sang in the tree.",
    "The fox ran across the field.",
    "A horse galloped over the hill.",
    "The duck swam across the pond.",
    "The cat chased the bird away.",
]


def make_src(items, name="src"):
    node = Node.create_node(NodeType.TEXT, name)
    node._parms["text_string"].set(str(items).replace("'", '"'))
    node._parms["pass_through"].set(False)
    return node


def make_train(state_size=2, retain_newlines=False):
    node = Node.create_node(NodeType.MARKOV_TRAIN, "train")
    node._parms["state_size"].set(state_size)
    node._parms["retain_newlines"].set(retain_newlines)
    return node


def test_output_is_single_json_string():
    src = make_src(CORPUS)
    train = make_train()
    train.set_input(0, src)
    train.cook()
    result = train._output
    assert len(result) == 1
    # Should be valid JSON
    obj = json.loads(result[0])
    assert isinstance(obj, dict)


def test_model_deserializes():
    src = make_src(CORPUS)
    train = make_train(state_size=2)
    train.set_input(0, src)
    train.cook()
    model = markovify.Text.from_json(train._output[0])
    assert model is not None


def test_state_size_parameter():
    src = make_src(CORPUS)
    train1 = make_train(state_size=1)
    train1.set_input(0, src)
    train1.cook()
    json1 = json.loads(train1._output[0])

    NodeEnvironment.get_instance().nodes.clear()
    src2 = Node.create_node(NodeType.TEXT, "src2")
    src2._parms["text_string"].set(str(CORPUS).replace("'", '"'))
    src2._parms["pass_through"].set(False)
    train2 = Node.create_node(NodeType.MARKOV_TRAIN, "train2")
    train2._parms["state_size"].set(3)
    train2.set_input(0, src2)
    train2.cook()
    json2 = json.loads(train2._output[0])

    assert json1 != json2


def test_empty_input_returns_error():
    src = make_src('[]')
    train = make_train()
    train.set_input(0, src)
    train.cook()
    assert any("error" in s.lower() for s in train._output)
