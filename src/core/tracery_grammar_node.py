import hashlib
import json
import random
import re
import time
from typing import Dict, List, Optional

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType

_SYMBOL_RE = re.compile(r'#([^#]+)#')
_MAX_DEPTH = 20


def _apply_modifier(word: str, modifier: str) -> str:
    """Apply a Tracery modifier to a word."""
    m = modifier.strip().lower()
    if m == "capitalize":
        return word.capitalize()
    if m == "a":
        article = "an" if word and word[0].lower() in "aeiou" else "a"
        return f"{article} {word}"
    if m == "s":
        if word.endswith(("s", "sh", "ch", "x", "z")):
            return word + "es"
        return word + "s"
    if m == "ed":
        if word.endswith("e"):
            return word + "d"
        if len(word) > 1 and word[-1] not in "aeiou" and word[-2] in "aeiou":
            return word + word[-1] + "ed"
        return word + "ed"
    return word  # unknown modifier — pass through


def _expand(symbol: str, grammar: Dict[str, List[str]], rng: random.Random, depth: int = 0) -> str:
    """Recursively expand a symbol using the grammar."""
    if depth > _MAX_DEPTH:
        return f"#{symbol}#"

    if symbol not in grammar:
        return f"#{symbol}#"

    template = rng.choice(grammar[symbol])

    def replace_match(m) -> str:
        full = m.group(1)
        # Handle modifiers: #symbol.modifier1.modifier2#
        parts = full.split(".")
        sym = parts[0]
        modifiers = parts[1:]
        result = _expand(sym, grammar, rng, depth + 1)
        for mod in modifiers:
            result = _apply_modifier(result, mod)
        return result

    return _SYMBOL_RE.sub(replace_match, template)


class TraceryGrammarNode(Node):
    """Expand a Tracery-style context-free grammar into text.

    Input: List of strings forming a JSON grammar definition (lines joined before parsing).
    Output: List of generated strings.

    start_symbol: Symbol to begin expansion from. Default 'origin'.
    count: Number of expansions to generate. Default 5.
    seed: Random seed (-1 = truly random).

    Supported modifiers: .capitalize, .a (a/an), .s (pluralize), .ed (past tense).
    """

    GLYPH = '⊕'
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "start_symbol": Parm("start_symbol", ParameterType.STRING, self),
            "count": Parm("count", ParameterType.INT, self),
            "seed": Parm("seed", ParameterType.INT, self),
        })
        self._parms["start_symbol"].set("origin")
        self._parms["count"].set(5)
        self._parms["seed"].set(-1)

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        start_symbol = self._parms["start_symbol"].eval().strip()
        count = max(1, self._parms["count"].eval())
        seed = self._parms["seed"].eval()

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        json_text = "\n".join(input_data)
        try:
            grammar: Dict[str, List[str]] = json.loads(json_text)
            if not isinstance(grammar, dict):
                raise ValueError("Grammar must be a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            self._output = [f"[TraceryGrammar error] Could not parse grammar JSON: {e}"]
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        if start_symbol not in grammar:
            self._output = [f"[TraceryGrammar error] Start symbol '{start_symbol}' not found in grammar"]
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        rng = random.Random() if seed == -1 else random.Random(seed)
        self._output = [_expand(start_symbol, grammar, rng) for _ in range(count)]

        self._param_hash = self._calculate_hash(start_symbol + str(count) + str(seed))
        self._input_hash = self._calculate_hash(json_text)
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            start_symbol = self._parms["start_symbol"].raw_value()
            count = self._parms["count"].raw_value()
            seed = self._parms["seed"].raw_value()
            new_param_hash = self._calculate_hash(str(start_symbol) + str(count) + str(seed))
            input_data = self.inputs()[0].output_node().get_output() if self.inputs() else []
            new_input_hash = self._calculate_hash(str(input_data))
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "Grammar JSON"}

    def output_names(self) -> Dict[int, str]:
        return {0: "Generated Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
