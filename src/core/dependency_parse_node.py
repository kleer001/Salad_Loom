import hashlib
import time
from typing import Dict, List, Optional, Set

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp

_DEFAULT_PRESERVE = "det,prep,aux,cc,punct,mark"


class DependencyParseNode(Node):
    """Extract syntactic dependency trees using spaCy.

    output_format: 'tree' (indented tree), 'flat' (word/POS/DEP/head), 'skeleton' (dep-role slots, default).
    preserve: Comma-separated dependency labels to keep as literal text in skeleton mode.
    """

    GLYPH = "⎇"
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "output_format": Parm("output_format", ParameterType.STRING, self),
            "preserve": Parm("preserve", ParameterType.STRING, self),
        })
        self._parms["output_format"].set("skeleton")
        self._parms["preserve"].set(_DEFAULT_PRESERVE)

    def _format_tree(self, doc) -> str:
        lines = []
        for token in doc:
            indent = "  " * token.i
            lines.append(f"{indent}{token.text}/{token.pos_}/{token.dep_}")
        return "\n".join(lines)

    def _format_flat(self, doc) -> str:
        parts = []
        for token in doc:
            parts.append(f"{token.text}/{token.pos_}/{token.dep_}/{token.head.text}")
        return " ".join(parts)

    def _format_skeleton(self, doc, preserve_deps: Set[str]) -> str:
        result = []
        for token in doc:
            if token.dep_ in preserve_deps or not token.is_alpha:
                result.append(token.text)
            else:
                result.append(f"[{token.dep_}]")
        return " ".join(result)

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        output_format = self._parms["output_format"].eval().strip().lower()
        preserve_str = self._parms["preserve"].eval()
        preserve_deps = {d.strip() for d in preserve_str.split(",") if d.strip()}

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        try:
            nlp = _get_nlp()
        except Exception as e:
            self._output = [f"[DependencyParse error] Could not load spaCy model: {e}"]
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        results = []
        for s in input_data:
            doc = nlp(s)
            if output_format == "tree":
                results.append(self._format_tree(doc))
            elif output_format == "flat":
                results.append(self._format_flat(doc))
            else:
                results.append(self._format_skeleton(doc, preserve_deps))

        self._output = results
        self._param_hash = self._calculate_hash(output_format + preserve_str)
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            fmt = self._parms["output_format"].raw_value()
            preserve = self._parms["preserve"].raw_value()
            new_param_hash = self._calculate_hash(str(fmt) + str(preserve))
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
        return {0: "Parsed Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
