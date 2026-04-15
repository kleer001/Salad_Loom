import hashlib
import random
import time
from typing import Dict, List, Optional

import markovify

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType


class MarkovGenerateNode(Node):
    """Generate text from a trained Markov model.

    Expects a list containing a single JSON-serialised model string
    (as produced by MarkovTrainNode). Outputs generated sentences.

    count: Number of sentences to generate. Default 10.
    max_chars: Max characters per sentence. 0 = no limit. Default 280.
    tries: Attempts per sentence before giving up. Default 100.
    seed: Random seed (-1 = truly random).
    """

    GLYPH = 'Ⓖ'
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "count": Parm("count", ParameterType.INT, self),
            "max_chars": Parm("max_chars", ParameterType.INT, self),
            "tries": Parm("tries", ParameterType.INT, self),
            "seed": Parm("seed", ParameterType.INT, self),
        })
        self._parms["count"].set(10)
        self._parms["max_chars"].set(280)
        self._parms["tries"].set(100)
        self._parms["seed"].set(-1)

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        count = max(1, self._parms["count"].eval())
        max_chars = self._parms["max_chars"].eval()
        tries = max(1, self._parms["tries"].eval())
        seed = self._parms["seed"].eval()

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        if not input_data or not input_data[0].strip():
            self._output = ["[MarkovGenerate error] No model JSON in input"]
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        model_json = input_data[0]

        try:
            model = markovify.Text.from_json(model_json)
        except Exception as e:
            self._output = [f"[MarkovGenerate error] Could not load model: {e}"]
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        if seed != -1:
            random.seed(seed)

        results: List[str] = []
        for _ in range(count):
            if max_chars > 0:
                sentence = model.make_short_sentence(max_chars, tries=tries)
            else:
                sentence = model.make_sentence(tries=tries)
            if sentence:
                results.append(sentence)

        self._output = results if results else ["[MarkovGenerate] No sentences generated"]

        self._param_hash = self._calculate_hash(str(count) + str(max_chars) + str(tries) + str(seed))
        self._input_hash = self._calculate_hash(model_json)
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            count = self._parms["count"].raw_value()
            max_chars = self._parms["max_chars"].raw_value()
            tries = self._parms["tries"].raw_value()
            seed = self._parms["seed"].raw_value()
            new_param_hash = self._calculate_hash(str(count) + str(max_chars) + str(tries) + str(seed))
            input_data = self.inputs()[0].output_node().get_output() if self.inputs() else []
            model_json = input_data[0] if input_data else ""
            new_input_hash = self._calculate_hash(model_json)
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "Model JSON"}

    def output_names(self) -> Dict[int, str]:
        return {0: "Generated Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
