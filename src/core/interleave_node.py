import hashlib
import re
import time
from itertools import cycle
from typing import Dict, List, Tuple

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType


class InterleaveNode(Node):
    """Weave two input lists together alternately.

    mode='items': A1, B1, A2, B2, ... (default)
    mode='words': Interleave words from paired strings.
    mode='sentences': Interleave sentences from paired strings.
    ratio: Pattern like '2:1' — take 2 from A, 1 from B. Default '1:1'.
    Shorter list is cycled to match the longer.
    """

    GLYPH = '⇅'
    GROUP = FunctionalGroup.LIST
    SINGLE_INPUT = False
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "mode": Parm("mode", ParameterType.STRING, self),
            "ratio": Parm("ratio", ParameterType.STRING, self),
        })
        self._parms["mode"].set("items")
        self._parms["ratio"].set("1:1")

    def _parse_ratio(self, ratio_str: str) -> Tuple[int, int]:
        parts = ratio_str.strip().split(":")
        if len(parts) == 2:
            try:
                a, b = int(parts[0]), int(parts[1])
                if a > 0 and b > 0:
                    return a, b
            except ValueError:
                pass
        return 1, 1

    def _interleave_lists(self, list_a: List[str], list_b: List[str], take_a: int, take_b: int) -> List[str]:
        if not list_a and not list_b:
            return []
        if not list_a:
            return list(list_b)
        if not list_b:
            return list(list_a)

        result = []
        longer_len = max(len(list_a), len(list_b))
        cy_a = cycle(list_a)
        cy_b = cycle(list_b)
        total_needed = longer_len * (take_a + take_b)
        produced = 0
        while produced < total_needed:
            for _ in range(take_a):
                result.append(next(cy_a))
                produced += 1
            for _ in range(take_b):
                result.append(next(cy_b))
                produced += 1
        return result[:max(len(list_a), len(list_b)) * (take_a + take_b) // max(take_a, take_b)]

    def _split_sentences(self, s: str) -> List[str]:
        return [sent.strip() for sent in re.split(r'(?<=[.!?])\s+', s.strip()) if sent.strip()]

    def _interleave_items(self, list_a: List[str], list_b: List[str], take_a: int, take_b: int) -> List[str]:
        return self._interleave_lists(list_a, list_b, take_a, take_b)

    def _interleave_words(self, list_a: List[str], list_b: List[str], take_a: int, take_b: int) -> List[str]:
        result = []
        pairs = zip(list_a, list_b) if len(list_a) <= len(list_b) else zip(
            list_a, cycle(list_b))
        if len(list_a) < len(list_b):
            pairs = zip(cycle(list_a), list_b)
        else:
            pairs = zip(list_a, cycle(list_b))
        for a_str, b_str in pairs:
            words_a = a_str.split()
            words_b = b_str.split()
            merged = self._interleave_lists(words_a, words_b, take_a, take_b)
            result.append(" ".join(merged))
        return result

    def _interleave_sentences(self, list_a: List[str], list_b: List[str], take_a: int, take_b: int) -> List[str]:
        result = []
        if len(list_a) <= len(list_b):
            pairs = zip(cycle(list_a), list_b)
        else:
            pairs = zip(list_a, cycle(list_b))
        for a_str, b_str in pairs:
            sents_a = self._split_sentences(a_str)
            sents_b = self._split_sentences(b_str)
            merged = self._interleave_lists(sents_a, sents_b, take_a, take_b)
            result.append(" ".join(merged))
        return result

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        mode = self._parms["mode"].eval().strip().lower()
        ratio_str = self._parms["ratio"].eval()
        take_a, take_b = self._parse_ratio(ratio_str)

        list_a: List[str] = []
        list_b: List[str] = []

        if 0 in self._inputs:
            raw = self._inputs[0].output_node().eval(requesting_node=self)
            list_a = [str(x) for x in raw] if isinstance(raw, list) else []
        if 1 in self._inputs:
            raw = self._inputs[1].output_node().eval(requesting_node=self)
            list_b = [str(x) for x in raw] if isinstance(raw, list) else []

        if mode == "words":
            self._output = self._interleave_words(list_a, list_b, take_a, take_b)
        elif mode == "sentences":
            self._output = self._interleave_sentences(list_a, list_b, take_a, take_b)
        else:
            self._output = self._interleave_items(list_a, list_b, take_a, take_b)

        self._param_hash = self._calculate_hash(mode + ratio_str)
        self._input_hash = self._calculate_hash(str(list_a) + str(list_b))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            mode = self._parms["mode"].raw_value()
            ratio = self._parms["ratio"].raw_value()
            new_param_hash = self._calculate_hash(str(mode) + str(ratio))
            a = self._inputs[0].output_node().get_output() if 0 in self._inputs else []
            b = self._inputs[1].output_node().get_output() if 1 in self._inputs else []
            new_input_hash = self._calculate_hash(str(a) + str(b))
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "List A", 1: "List B"}

    def output_names(self) -> Dict[int, str]:
        return {0: "Interleaved"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]", 1: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
