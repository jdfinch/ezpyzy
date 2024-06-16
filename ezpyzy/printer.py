
from __future__ import annotations

import dataclasses as dc
import re
import ezpyzy.ansi as an


@dc.dataclass
class Printer:
    ...



if __name__ == '__main__':


    ansi_sentence = f"{an.foreground_red}Hello {an.foreground_green}this is a {an.reset}test."
    sentence = an.strip(ansi_sentence)
    print(ansi_sentence, f"{len(ansi_sentence) = }", f"{an.length(ansi_sentence) = }")
    print(sentence, f"{len(sentence) = }")

    print([ansi_sentence[s:e] for s, e in an.parse(ansi_sentence)])