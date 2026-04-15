import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType

_DEFAULT_MODEL = Path(__file__).parent.parent.parent / "data" / "models" / "glove-wiki-gigaword-50.kv"

_wv = None
_wv_path: Optional[str] = None


def _get_wv(model_path: str):
    global _wv, _wv_path
    if _wv is None or _wv_path != model_path:
        from gensim.models import KeyedVectors
        _wv = KeyedVectors.load(model_path)
        _wv_path = model_path
    return _wv


def _cosine_similarity(v1, v2) -> float:
    import math
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def _score_sentence(sentence: str, wv, window: int) -> float:
    import re
    words = [w.lower() for w in re.findall(r"[a-zA-Z]+", sentence)]
    vectors = [wv[w] for w in words if w in wv]
    if len(vectors) < 2:
        return 0.0
    similarities = []
    for i in range(len(vectors) - window + 1):
        group = vectors[i:i + window]
        pairs = [(group[a], group[b]) for a in range(len(group)) for b in range(a + 1, len(group))]
        for v1, v2 in pairs:
            similarities.append(_cosine_similarity(v1, v2))
    return sum(similarities) / len(similarities) if similarities else 0.0


class CoherenceGateNode(Node):
    """Filter text by semantic coherence using word vector cosine similarity.

    min_coherence: Minimum score to pass. Default 0.1.
    max_coherence: Maximum score to pass. Default 0.7.
    window: Sliding window of consecutive words to compare. Default 3.
    model_path: Path to Gensim KeyedVectors .kv file. Defaults to bundled GloVe.

    The sweet spot for absurdist text is roughly 0.15-0.45.
    """

    GLYPH = "⊗"
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "min_coherence": Parm("min_coherence", ParameterType.FLOAT, self),
            "max_coherence": Parm("max_coherence", ParameterType.FLOAT, self),
            "window": Parm("window", ParameterType.INT, self),
            "model_path": Parm("model_path", ParameterType.STRING, self),
        })
        self._parms["min_coherence"].set(0.1)
        self._parms["max_coherence"].set(0.7)
        self._parms["window"].set(3)
        self._parms["model_path"].set("")

    def _resolve_model_path(self, override: str) -> str:
        if override.strip():
            return override.strip()
        return str(_DEFAULT_MODEL)

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        min_c = max(0.0, self._parms["min_coherence"].eval())
        max_c = min(1.0, self._parms["max_coherence"].eval())
        window = max(2, self._parms["window"].eval())
        model_path = self._resolve_model_path(self._parms["model_path"].eval())

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        try:
            wv = _get_wv(model_path)
        except Exception as e:
            self._output = [f"[CoherenceGate error] Could not load word vectors: {e}"]
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        results = []
        for s in input_data:
            score = _score_sentence(s, wv, window)
            if min_c <= score <= max_c:
                results.append(s)

        self._output = results
        self._param_hash = self._calculate_hash(
            str(min_c) + str(max_c) + str(window) + model_path
        )
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            mn = self._parms["min_coherence"].raw_value()
            mx = self._parms["max_coherence"].raw_value()
            w = self._parms["window"].raw_value()
            mp = self._parms["model_path"].raw_value()
            new_param_hash = self._calculate_hash(str(mn)+str(mx)+str(w)+str(mp))
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
        return {0: "Gated Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
