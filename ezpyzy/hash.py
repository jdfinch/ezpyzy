
from __future__ import annotations

import hashlib as hl
import base64 as b64


def hash(s: bytes|str):
    if isinstance(s, str):
        s = s.encode()
    return b64.standard_b64decode(hl.sha256(s).digest()).decode('ascii')