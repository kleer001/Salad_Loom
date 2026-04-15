import hashlib
import re
import time
from typing import Dict, List, Optional

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType

_cmu_dict = None

def _get_cmu_dict():
    global _cmu_dict
    if _cmu_dict is None:
        import nltk
        try:
            from nltk.corpus import cmudict
            _cmu_dict = cmudict.dict()
        except LookupError:
            nltk.download("cmudict", quiet=True)
            from nltk.corpus import cmudict
            _cmu_dict = cmudict.dict()
    return _cmu_dict


def _count_syllables(word: str, cmu: dict) -> int:
    phones = cmu.get(word.lower())
    if phones:
        return sum(1 for p in phones[0] if p[-1].isdigit())
    # Fallback: count vowel groups
    return max(1, len(re.findall(r"[aeiou]+", word.lower())))


def _alliteration_score(words: List[str]) -> float:
    if len(words) < 2:
        return 0.0
    consonant_pairs = 0
    for i in range(len(words) - 1):
        a = re.sub(r"[^a-z]", "", words[i].lower())
        b = re.sub(r"[^a-z]", "", words[i + 1].lower())
        if a and b and a[0] == b[0] and a[0] not in "aeiou":
            consonant_pairs += 1
    return consonant_pairs / (len(words) - 1)


def _assonance_score(words: List[str], cmu: dict) -> float:
    if len(words) < 2:
        return 0.0
    vowel_phonemes = []
    for w in words:
        phones = cmu.get(w.lower())
        if phones:
            stressed = [p[:-1] for p in phones[0] if p[-1] in "12"]
            vowel_phonemes.extend(stressed[:1])
    if len(vowel_phonemes) < 2:
        return 0.0
    matches = sum(
        1 for i in range(len(vowel_phonemes) - 1)
        if vowel_phonemes[i] == vowel_phonemes[i + 1]
    )
    return matches / (len(vowel_phonemes) - 1)


def _rhythm_score(words: List[str], cmu: dict) -> float:
    if len(words) < 2:
        return 0.0
    syllable_counts = [_count_syllables(w, cmu) for w in words]
    mean = sum(syllable_counts) / len(syllable_counts)
    variance = sum((x - mean) ** 2 for x in syllable_counts) / len(syllable_counts)
    std_dev = variance ** 0.5
    # Normalize: std_dev of ~1.5 → score 1.0
    return min(1.0, std_dev / 1.5)


class PhoneticFilterNode(Node):
    """Score and filter text by sound properties.

    mode: 'alliteration' | 'assonance' | 'rhythm' | 'any'.
    threshold: Minimum score (0.0-1.0) to pass. Default 0.3.
    invert: If True, keep strings BELOW threshold. Default False.
    """

    GLYPH = "♪"
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "mode": Parm("mode", ParameterType.STRING, self),
            "threshold": Parm("threshold", ParameterType.FLOAT, self),
            "invert": Parm("invert", ParameterType.TOGGLE, self),
        })
        self._parms["mode"].set("alliteration")
        self._parms["threshold"].set(0.3)
        self._parms["invert"].set(False)

    def _score(self, sentence: str, mode: str, cmu: dict) -> float:
        words = re.findall(r"[a-zA-Z']+", sentence)
        if not words:
            return 0.0
        if mode == "alliteration":
            return _alliteration_score(words)
        if mode == "assonance":
            return _assonance_score(words, cmu)
        if mode == "rhythm":
            return _rhythm_score(words, cmu)
        # "any" — average of all three
        scores = [
            _alliteration_score(words),
            _assonance_score(words, cmu),
            _rhythm_score(words, cmu),
        ]
        return sum(scores) / 3.0

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        mode = self._parms["mode"].eval().strip().lower()
        threshold = max(0.0, min(1.0, self._parms["threshold"].eval()))
        invert = self._parms["invert"].eval()

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        try:
            cmu = _get_cmu_dict()
        except Exception as e:
            self._output = [f"[PhoneticFilter error] Could not load CMU dict: {e}"]
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        results = []
        for s in input_data:
            score = self._score(s, mode, cmu)
            passes = score >= threshold
            if invert:
                passes = not passes
            if passes:
                results.append(s)

        self._output = results
        self._param_hash = self._calculate_hash(mode + str(threshold) + str(invert))
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            mode = self._parms["mode"].raw_value()
            threshold = self._parms["threshold"].raw_value()
            invert = self._parms["invert"].raw_value()
            new_param_hash = self._calculate_hash(str(mode) + str(threshold) + str(invert))
            input_data = self.inputs()[0].output_node().get_output() if self.inputs() else []
            new_input_hash = self._calculate_hash(str(input_data))
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "Input Text"}

    def output_names(self) -> Dict[int, str]:
        return {0: "Filtered Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
