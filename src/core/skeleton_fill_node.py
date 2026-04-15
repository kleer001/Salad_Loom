import hashlib
import random
import re
import time
from collections import defaultdict
from typing import Dict, List, Optional

import nltk

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType

_SLOT_PATTERN = re.compile(r'\[([A-Z$]+)\]')


class SkeletonFillNode(Node):
    """Fill tagged slots in skeleton strings with words from a word pool.

    Input 0: Skeleton strings (containing [TAG] markers from SkeletonExtractNode).
    Input 1: Word pool — either 'word/TAG' per line, or plain words (auto-tagged).

    mode: 'random' (default), 'sequential' (cycle in order), 'weighted' (prefer rare words).
    seed: Random seed (-1 = truly random).
    allow_repeats: Whether the same word can fill multiple slots. Default True.
    """

    GLYPH = '⊟'
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = False
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "mode": Parm("mode", ParameterType.STRING, self),
            "seed": Parm("seed", ParameterType.INT, self),
            "allow_repeats": Parm("allow_repeats", ParameterType.TOGGLE, self),
        })
        self._parms["mode"].set("random")
        self._parms["seed"].set(-1)
        self._parms["allow_repeats"].set(True)

    def _parse_word_pool(self, pool_lines: List[str]) -> Dict[str, List[str]]:
        """Parse word pool into {tag: [words]}.

        Accepts 'word/TAG' format or plain words (auto-tagged via NLTK).
        """
        buckets: Dict[str, List[str]] = defaultdict(list)
        plain_words = []

        for line in pool_lines:
            line = line.strip()
            if not line:
                continue
            if "/" in line:
                parts = line.rsplit("/", 1)
                if len(parts) == 2:
                    word, tag = parts[0].strip(), parts[1].strip().upper()
                    buckets[tag].append(word)
                    continue
            plain_words.append(line)

        if plain_words:
            try:
                tagged = nltk.pos_tag(plain_words)
                for word, tag in tagged:
                    buckets[tag].append(word)
            except Exception:
                for word in plain_words:
                    buckets["NN"].append(word)

        return dict(buckets)

    def _make_rng(self, seed: int) -> random.Random:
        if seed == -1:
            return random.Random()
        return random.Random(seed)

    def _fill_skeleton(
        self,
        skeleton: str,
        buckets: Dict[str, List[str]],
        mode: str,
        rng: random.Random,
        allow_repeats: bool,
        sequential_counters: Dict[str, int],
    ) -> str:
        def replace_slot(match) -> str:
            tag = match.group(1)
            candidates = buckets.get(tag, [])
            if not candidates:
                return match.group(0)  # leave slot unfilled

            if mode == "sequential":
                idx = sequential_counters.get(tag, 0) % len(candidates)
                sequential_counters[tag] = idx + 1
                return candidates[idx]

            if not allow_repeats:
                available = [w for w in candidates]
                if available:
                    word = rng.choice(available)
                    candidates.remove(word)
                    return word
                return match.group(0)

            return rng.choice(candidates)

        return _SLOT_PATTERN.sub(replace_slot, skeleton)

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        mode = self._parms["mode"].eval().strip().lower()
        seed = self._parms["seed"].eval()
        allow_repeats = self._parms["allow_repeats"].eval()

        skeletons: List[str] = []
        pool_lines: List[str] = []

        if 0 in self._inputs:
            raw = self._inputs[0].output_node().eval(requesting_node=self)
            skeletons = [str(x) for x in raw] if isinstance(raw, list) else []
        if 1 in self._inputs:
            raw = self._inputs[1].output_node().eval(requesting_node=self)
            pool_lines = [str(x) for x in raw] if isinstance(raw, list) else []

        if not skeletons:
            self._output = []
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        buckets = self._parse_word_pool(pool_lines)
        rng = self._make_rng(seed)
        sequential_counters: Dict[str, int] = {}

        self._output = [
            self._fill_skeleton(s, buckets, mode, rng, allow_repeats, sequential_counters)
            for s in skeletons
        ]

        self._param_hash = self._calculate_hash(mode + str(seed) + str(allow_repeats))
        self._input_hash = self._calculate_hash(str(skeletons) + str(pool_lines))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            mode = self._parms["mode"].raw_value()
            seed = self._parms["seed"].raw_value()
            allow_repeats = self._parms["allow_repeats"].raw_value()
            new_param_hash = self._calculate_hash(str(mode) + str(seed) + str(allow_repeats))
            skel = self._inputs[0].output_node().get_output() if 0 in self._inputs else []
            pool = self._inputs[1].output_node().get_output() if 1 in self._inputs else []
            new_input_hash = self._calculate_hash(str(skel) + str(pool))
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "Skeletons", 1: "Word Pool"}

    def output_names(self) -> Dict[int, str]:
        return {0: "Filled Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]", 1: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
