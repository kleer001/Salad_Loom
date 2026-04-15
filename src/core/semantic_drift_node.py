import hashlib
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

import nltk

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType

_DEFAULT_MODEL = Path(__file__).parent.parent.parent / "data" / "models" / "glove-wiki-gigaword-50.kv"
_DEFAULT_TARGET_POS = "NN,NNS,JJ,VB,VBD,VBG"

_wv = None
_wv_path: Optional[str] = None


def _get_wv(model_path: str):
    global _wv, _wv_path
    if _wv is None or _wv_path != model_path:
        from gensim.models import KeyedVectors
        _wv = KeyedVectors.load(model_path)
        _wv_path = model_path
    return _wv


class SemanticDriftNode(Node):
    """Gradually replace words with semantically adjacent ones via word vectors.

    drift_rate: Fraction of target words to replace per call. Default 0.1.
    drift_distance: 0.0 = nearest synonym, 1.0 = furthest. Default 0.3.
    target_pos: Comma-separated POS tags to consider for replacement.
    seed: Random seed (-1 = truly random).
    model_path: Path to a Gensim KeyedVectors .kv file. Defaults to bundled GloVe model.
    """

    GLYPH = "~"
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "drift_rate": Parm("drift_rate", ParameterType.FLOAT, self),
            "drift_distance": Parm("drift_distance", ParameterType.FLOAT, self),
            "target_pos": Parm("target_pos", ParameterType.STRING, self),
            "seed": Parm("seed", ParameterType.INT, self),
            "model_path": Parm("model_path", ParameterType.STRING, self),
        })
        self._parms["drift_rate"].set(0.1)
        self._parms["drift_distance"].set(0.3)
        self._parms["target_pos"].set(_DEFAULT_TARGET_POS)
        self._parms["seed"].set(-1)
        self._parms["model_path"].set("")

    def _resolve_model_path(self, override: str) -> str:
        if override.strip():
            return override.strip()
        return str(_DEFAULT_MODEL)

    def _drift_string(self, s: str, target_tags: Set[str], drift_rate: float,
                      drift_distance: float, wv, rng: random.Random) -> str:
        tokens = nltk.word_tokenize(s)
        tagged = nltk.pos_tag(tokens)
        result = []
        for word, tag in tagged:
            if tag in target_tags and word.isalpha() and rng.random() < drift_rate:
                lower = word.lower()
                if lower in wv:
                    neighbors = wv.most_similar(lower, topn=50)
                    # drift_distance 0.0 = pick from top; 1.0 = pick from bottom of list
                    idx = int(drift_distance * (len(neighbors) - 1))
                    replacement = neighbors[idx][0]
                    if word[0].isupper():
                        replacement = replacement.capitalize()
                    result.append(replacement)
                    continue
            result.append(word)
        text = " ".join(result)
        for punct in (".", ",", "!", "?", ";", ":", ")", "]", "'s"):
            text = text.replace(" " + punct, punct)
        return text

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        drift_rate = max(0.0, min(0.5, self._parms["drift_rate"].eval()))
        drift_distance = max(0.0, min(1.0, self._parms["drift_distance"].eval()))
        target_pos_str = self._parms["target_pos"].eval()
        target_tags = {t.strip() for t in target_pos_str.split(",") if t.strip()}
        seed = self._parms["seed"].eval()
        model_path = self._resolve_model_path(self._parms["model_path"].eval())

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        try:
            wv = _get_wv(model_path)
        except Exception as e:
            self._output = [f"[SemanticDrift error] Could not load word vectors: {e}"]
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        rng = random.Random() if seed == -1 else random.Random(seed)
        self._output = [
            self._drift_string(s, target_tags, drift_rate, drift_distance, wv, rng)
            for s in input_data
        ]

        self._param_hash = self._calculate_hash(
            str(drift_rate) + str(drift_distance) + target_pos_str + str(seed) + model_path
        )
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            dr = self._parms["drift_rate"].raw_value()
            dd = self._parms["drift_distance"].raw_value()
            tp = self._parms["target_pos"].raw_value()
            s = self._parms["seed"].raw_value()
            mp = self._parms["model_path"].raw_value()
            new_param_hash = self._calculate_hash(str(dr)+str(dd)+str(tp)+str(s)+str(mp))
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
        return {0: "Drifted Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
