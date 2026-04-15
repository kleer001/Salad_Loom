import hashlib
import random
import re
import time
from typing import Dict, List

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType


class ShuffleNode(Node):
    """Randomly reorder items in the input list.

    mode='items': Shuffle the list items themselves (default).
    mode='words': Split each string into words, shuffle words, rejoin.
    mode='sentences': Split each string into sentences, shuffle sentences, rejoin.
    seed=-1 means truly random; any other int gives deterministic output.
    """

    GLYPH = '⇌'
    GROUP = FunctionalGroup.LIST
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "seed": Parm("seed", ParameterType.INT, self),
            "mode": Parm("mode", ParameterType.STRING, self),
        })
        self._parms["seed"].set(-1)
        self._parms["mode"].set("items")

    def _make_rng(self, seed: int) -> random.Random:
        if seed == -1:
            return random.Random()
        return random.Random(seed)

    def _shuffle_items(self, items: List[str], rng: random.Random) -> List[str]:
        result = list(items)
        rng.shuffle(result)
        return result

    def _shuffle_words(self, items: List[str], rng: random.Random) -> List[str]:
        result = []
        for s in items:
            words = s.split()
            rng.shuffle(words)
            result.append(" ".join(words))
        return result

    def _shuffle_sentences(self, items: List[str], rng: random.Random) -> List[str]:
        result = []
        for s in items:
            sentences = re.split(r'(?<=[.!?])\s+', s.strip())
            sentences = [sent for sent in sentences if sent]
            rng.shuffle(sentences)
            result.append(" ".join(sentences))
        return result

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        seed = self._parms["seed"].eval()
        mode = self._parms["mode"].eval().strip().lower()

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            if isinstance(raw, list):
                input_data = [str(x) for x in raw]
            else:
                self._output = ["[ShuffleNode error] Input must be List[str]"]
                self.set_state(NodeState.UNCHANGED)
                self._last_cook_time = (time.time() - start_time) * 1000
                return

        rng = self._make_rng(seed)

        if mode == "words":
            self._output = self._shuffle_words(input_data, rng)
        elif mode == "sentences":
            self._output = self._shuffle_sentences(input_data, rng)
        else:
            self._output = self._shuffle_items(input_data, rng)

        self._param_hash = self._calculate_hash(str(seed) + mode)
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            seed = self._parms["seed"].raw_value()
            mode = self._parms["mode"].raw_value()
            new_param_hash = self._calculate_hash(str(seed) + str(mode))
            input_data = self.inputs()[0].output_node().get_output() if self.inputs() else []
            new_input_hash = self._calculate_hash(str(input_data))
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "Input List"}

    def output_names(self) -> Dict[int, str]:
        return {0: "Shuffled List"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
