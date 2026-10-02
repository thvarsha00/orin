"""Small helpers shared by AI providers."""
from typing import AsyncIterator

_OPEN, _CLOSE = "<think>", "</think>"


def _partial_suffix(text: str, tag: str) -> int:
    """Length of the longest proper prefix of `tag` that `text` ends with (a tag split across chunks)."""
    for k in range(min(len(tag) - 1, len(text)), 0, -1):
        if text.endswith(tag[:k]):
            return k
    return 0


async def strip_think(stream: AsyncIterator[str]) -> AsyncIterator[str]:
    """Drop <think>...</think> reasoning blocks that some reasoning/vision models emit inline,
    so students only ever see the answer. Works when a tag is split across streamed chunks."""
    buf, inside, started = "", False, False
    async for chunk in stream:
        buf += chunk
        out = ""
        while True:
            if inside:
                i = buf.find(_CLOSE)
                if i == -1:
                    buf = buf[len(buf) - _partial_suffix(buf, _CLOSE):]
                    break
                buf, inside = buf[i + len(_CLOSE):], False
            else:
                i = buf.find(_OPEN)
                if i == -1:
                    keep = _partial_suffix(buf, _OPEN)
                    out += buf[:len(buf) - keep]
                    buf = buf[len(buf) - keep:]
                    break
                out += buf[:i]
                buf, inside = buf[i + len(_OPEN):], True
        if out:
            if not started:
                out = out.lstrip()
            if out:
                started = True
                yield out
    if not inside and buf:
        yield buf if started else buf.lstrip()
