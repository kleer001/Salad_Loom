import hashlib
import time
from typing import Dict, List

import markovify

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType


class MarkovTrainNode(Node):
    """Build a Markov chain model from input text.

    Accepts a list of strings as the training corpus. Outputs a list
    containing a single string: the JSON-serialised Markov model, suitable
    for piping into MarkovGenerateNode.

    state_size: Number of words in the prefix (1-4). Default 2.
    retain_newlines: Treat newlines as tokens. Default False.
    """

    GLYPH = 'Ⓜ'
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "state_size": Parm("state_size", ParameterType.INT, self),
            "retain_newlines": Parm("retain_newlines", ParameterType.TOGGLE, self),
        })
        self._parms["state_size"].set(2)
        self._parms["retain_newlines"].set(False)

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        state_size = max(1, min(4, self._parms["state_size"].eval()))
        retain_newlines = self._parms["retain_newlines"].eval()

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        if not input_data:
            self._output = ["[MarkovTrain error] No input data"]
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        corpus = "\n".join(input_data) if retain_newlines else " ".join(input_data)

        try:
            model = markovify.Text(corpus, state_size=state_size, retain_original=False)
            self._output = [model.to_json()]
        except Exception as e:
            self._output = [f"[MarkovTrain error] {e}"]

        self._param_hash = self._calculate_hash(str(state_size) + str(retain_newlines))
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            state_size = self._parms["state_size"].raw_value()
            retain = self._parms["retain_newlines"].raw_value()
            new_param_hash = self._calculate_hash(str(state_size) + str(retain))
            input_data = self.inputs()[0].output_node().get_output() if self.inputs() else []
            new_input_hash = self._calculate_hash(str(input_data))
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "Training Corpus"}

    def output_names(self) -> Dict[int, str]:
        return {0: "Model JSON"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
