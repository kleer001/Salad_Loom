import hashlib
import re
import time
from typing import Dict, List

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType


_FLAG_MAP = {
    "ignorecase": re.IGNORECASE,
    "multiline": re.MULTILINE,
    "dotall": re.DOTALL,
}


class RegexReplaceNode(Node):
    """Find-and-replace using regular expressions.

    pattern: Regex pattern to match. Required.
    replacement: Replacement string. Supports backreferences. Default '' (deletion).
    count: Max replacements per string. 0 = all. Default 0.
    flags: Comma-separated flags: ignorecase, multiline, dotall. Default ''.
    """

    GLYPH = 'Ʀ'
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "pattern": Parm("pattern", ParameterType.STRING, self),
            "replacement": Parm("replacement", ParameterType.STRING, self),
            "count": Parm("count", ParameterType.INT, self),
            "flags": Parm("flags", ParameterType.STRING, self),
        })
        self._parms["pattern"].set("")
        self._parms["replacement"].set("")
        self._parms["count"].set(0)
        self._parms["flags"].set("")

    def _parse_flags(self, flags_str: str) -> int:
        combined = 0
        for token in flags_str.split(","):
            token = token.strip().lower()
            if token in _FLAG_MAP:
                combined |= _FLAG_MAP[token]
        return combined

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        pattern = self._parms["pattern"].eval()
        replacement = self._parms["replacement"].eval()
        count = max(0, self._parms["count"].eval())
        flags_str = self._parms["flags"].eval()
        flags = self._parse_flags(flags_str)

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        if not pattern:
            self._output = input_data
        else:
            try:
                compiled = re.compile(pattern, flags)
                self._output = [compiled.sub(replacement, s, count=count) for s in input_data]
            except re.error as e:
                self._output = [f"[RegexReplace error] {e}"] * max(1, len(input_data))

        self._param_hash = self._calculate_hash(pattern + replacement + str(count) + flags_str)
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            pattern = self._parms["pattern"].raw_value()
            replacement = self._parms["replacement"].raw_value()
            count = self._parms["count"].raw_value()
            flags = self._parms["flags"].raw_value()
            new_param_hash = self._calculate_hash(str(pattern) + str(replacement) + str(count) + str(flags))
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
        return {0: "Output Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
