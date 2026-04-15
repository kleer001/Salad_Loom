import hashlib
import time
from itertools import cycle
from typing import Dict, List

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType


class FoldInNode(Node):
    """Burroughs/Gysin fold-in technique.

    Takes two text inputs, pairs their lines, splits each line at split_point,
    and produces: left-half of A + right-half of B.

    split_point: Fraction of line length at which to fold. Default 0.5.
    mode: 'characters' (default, true to original) or 'words'.
    """

    GLYPH = '⧓'
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = False
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "split_point": Parm("split_point", ParameterType.FLOAT, self),
            "mode": Parm("mode", ParameterType.STRING, self),
        })
        self._parms["split_point"].set(0.5)
        self._parms["mode"].set("characters")

    def _fold_characters(self, line_a: str, line_b: str, split_point: float) -> str:
        cut_a = max(1, int(len(line_a) * split_point))
        cut_b = max(1, int(len(line_b) * (1.0 - split_point)))
        left = line_a[:cut_a]
        right = line_b[len(line_b) - cut_b:] if cut_b <= len(line_b) else line_b
        return left + " " + right

    def _fold_words(self, line_a: str, line_b: str, split_point: float) -> str:
        words_a = line_a.split()
        words_b = line_b.split()
        cut_a = max(1, int(len(words_a) * split_point))
        cut_b = max(1, int(len(words_b) * (1.0 - split_point)))
        left = " ".join(words_a[:cut_a])
        right = " ".join(words_b[len(words_b) - cut_b:]) if cut_b <= len(words_b) else " ".join(words_b)
        return left + " " + right

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        split_point = max(0.1, min(0.9, self._parms["split_point"].eval()))
        mode = self._parms["mode"].eval().strip().lower()

        list_a: List[str] = []
        list_b: List[str] = []

        if 0 in self._inputs:
            raw = self._inputs[0].output_node().eval(requesting_node=self)
            list_a = [str(x) for x in raw] if isinstance(raw, list) else []
        if 1 in self._inputs:
            raw = self._inputs[1].output_node().eval(requesting_node=self)
            list_b = [str(x) for x in raw] if isinstance(raw, list) else []

        if not list_a or not list_b:
            self._output = list_a or list_b
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        # Cycle the shorter list
        longer_len = max(len(list_a), len(list_b))
        cy_a = cycle(list_a)
        cy_b = cycle(list_b)

        result = []
        fold_fn = self._fold_words if mode == "words" else self._fold_characters
        for _ in range(longer_len):
            line_a = next(cy_a)
            line_b = next(cy_b)
            result.append(fold_fn(line_a, line_b, split_point))

        self._output = result
        self._param_hash = self._calculate_hash(str(split_point) + mode)
        self._input_hash = self._calculate_hash(str(list_a) + str(list_b))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            split_point = self._parms["split_point"].raw_value()
            mode = self._parms["mode"].raw_value()
            new_param_hash = self._calculate_hash(str(split_point) + str(mode))
            a = self._inputs[0].output_node().get_output() if 0 in self._inputs else []
            b = self._inputs[1].output_node().get_output() if 1 in self._inputs else []
            new_input_hash = self._calculate_hash(str(a) + str(b))
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "Text A", 1: "Text B"}

    def output_names(self) -> Dict[int, str]:
        return {0: "Folded Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]", 1: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
