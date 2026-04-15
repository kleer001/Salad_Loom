import hashlib
import random
import re
import time
from typing import Dict, List

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType


class RepetitionInjectorNode(Node):
    """Create obsessive, stuttering text by randomly repeating words, phrases, or sentences.

    mode: 'word' (default), 'phrase' (2-4 word chunks), 'sentence'.
    density: Probability of repeating any given element. Default 0.15.
    max_repeats: Maximum extra copies to insert. Default 3.
    seed: Random seed (-1 = truly random).
    """

    GLYPH = '↺'
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "mode": Parm("mode", ParameterType.STRING, self),
            "density": Parm("density", ParameterType.FLOAT, self),
            "max_repeats": Parm("max_repeats", ParameterType.INT, self),
            "seed": Parm("seed", ParameterType.INT, self),
        })
        self._parms["mode"].set("word")
        self._parms["density"].set(0.15)
        self._parms["max_repeats"].set(3)
        self._parms["seed"].set(-1)

    def _make_rng(self, seed: int) -> random.Random:
        return random.Random() if seed == -1 else random.Random(seed)

    def _inject_words(self, s: str, density: float, max_repeats: int, rng: random.Random) -> str:
        words = s.split()
        result = []
        for word in words:
            result.append(word)
            if rng.random() < density:
                repeats = rng.randint(1, max(1, max_repeats))
                result.extend([word] * repeats)
        return " ".join(result)

    def _inject_phrases(self, s: str, density: float, max_repeats: int, rng: random.Random) -> str:
        words = s.split()
        if len(words) < 2:
            return self._inject_words(s, density, max_repeats, rng)
        result = []
        i = 0
        while i < len(words):
            phrase_len = rng.randint(2, min(4, len(words) - i))
            phrase = words[i:i + phrase_len]
            result.extend(phrase)
            if rng.random() < density:
                repeats = rng.randint(1, max(1, max_repeats))
                for _ in range(repeats):
                    result.extend(phrase)
            i += phrase_len
        return " ".join(result)

    def _inject_sentences(self, s: str, density: float, max_repeats: int, rng: random.Random) -> str:
        sentences = [sent.strip() for sent in re.split(r'(?<=[.!?])\s+', s.strip()) if sent.strip()]
        if not sentences:
            return s
        result = []
        for sent in sentences:
            result.append(sent)
            if rng.random() < density:
                repeats = rng.randint(1, max(1, max_repeats))
                result.extend([sent] * repeats)
        return " ".join(result)

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        mode = self._parms["mode"].eval().strip().lower()
        density = max(0.0, min(1.0, self._parms["density"].eval()))
        max_repeats = max(1, min(10, self._parms["max_repeats"].eval()))
        seed = self._parms["seed"].eval()

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        rng = self._make_rng(seed)

        if mode == "phrase":
            fn = self._inject_phrases
        elif mode == "sentence":
            fn = self._inject_sentences
        else:
            fn = self._inject_words

        self._output = [fn(s, density, max_repeats, rng) for s in input_data]

        self._param_hash = self._calculate_hash(mode + str(density) + str(max_repeats) + str(seed))
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            mode = self._parms["mode"].raw_value()
            density = self._parms["density"].raw_value()
            max_repeats = self._parms["max_repeats"].raw_value()
            seed = self._parms["seed"].raw_value()
            new_param_hash = self._calculate_hash(str(mode) + str(density) + str(max_repeats) + str(seed))
            input_data = self.inputs()[0].output_node().get_output() if self.inputs() else []
            new_input_hash = self._calculate_hash(str(input_data))
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "Input Text"}

    def output_names(self) -> Dict[int, str]:
        return {0: "Stuttered Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
