
from __future__ import annotations

import dataclasses as dc
import ezpyzy.ansi as an


@dc.dataclass
class Printer:
    ...


"""
Animation:

Elements--
    - string id key for element
    - relative row
    - absolute col
    - animation generator (or None)
    - update

Chunking--
    - character by character effects
    - line by line effects
    - word by word effects
    
Color over time and location 

"""



if __name__ == '__main__':
    ansi_sentence = f"{an.color('red')}Hello {an.color('green')}this is a {an.reset}test."
    sentence = an.strip(ansi_sentence)
    print(ansi_sentence, f"{len(ansi_sentence) = }", f"{an.length(ansi_sentence) = }")
    print(sentence, f"{len(sentence) = }")
    print([ansi_sentence[s:e] for s, e in an.parse(ansi_sentence)])