"""Turn source lines into styled segments using Pygments."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from pygments.lexer import Lexer
from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
from pygments.lexers.special import TextLexer
from pygments.styles import get_style_by_name
from pygments.token import Comment, Keyword, Token, _TokenType
from pygments.util import ClassNotFound

# (hex colour or None, bold, italic)
Style = Tuple[Optional[str], bool, bool]
Segment = Tuple[str, Style]
PLAIN: Style = (None, False, False)


def get_lexer(alias: Optional[str], filename: str, text: str) -> Lexer:
    opts = {"stripnl": False, "stripall": False, "ensurenl": False}
    if alias:
        try:
            return get_lexer_by_name(alias, **opts)
        except ClassNotFound:
            pass
    try:
        return guess_lexer_for_filename(filename, text, **opts)
    except ClassNotFound:
        return TextLexer(**opts)


class Highlighter:
    def __init__(self, mode: str, theme: str) -> None:
        self.mode = mode
        self.style = get_style_by_name(theme) if mode == "color" else None
        self._cache: Dict[_TokenType, Style] = {}

    def style_for(self, ttype: _TokenType) -> Style:
        cached = self._cache.get(ttype)
        if cached is not None:
            return cached
        if self.mode == "mono":
            # Black-and-white printing: keywords bold, comments italic.
            style: Style = (None, ttype in Keyword, ttype in Comment)
        else:
            s = self.style.style_for_token(ttype)  # type: ignore[union-attr]
            color = s["color"].upper() if s["color"] else None
            if color in ("000000", "000"):
                color = None
            style = (color, bool(s["bold"]), bool(s["italic"]))
        self._cache[ttype] = style
        return style

    def lines(
        self, lines: List[str], alias: Optional[str], filename: str
    ) -> Tuple[List[List[Segment]], Optional[str]]:
        """Split ``lines`` into styled segments, one list per input line.

        Also returns the name of the lexer used (``None`` when not highlighting).
        """
        if self.mode == "none" or not lines:
            return [[(line, PLAIN)] if line else [] for line in lines], None
        text = "\n".join(lines)
        lexer = get_lexer(alias, filename, text)
        out: List[List[Segment]] = [[]]
        for ttype, value in lexer.get_tokens(text):
            if not value:
                continue
            style = self.style_for(ttype) if ttype is not Token.Text else PLAIN
            pieces = value.split("\n")
            for i, piece in enumerate(pieces):
                if i:
                    out.append([])
                if piece:
                    row = out[-1]
                    if row and row[-1][1] == style:
                        row[-1] = (row[-1][0] + piece, style)
                    else:
                        row.append((piece, style))
        # Lexers may add or drop a trailing newline; keep exactly one row per line.
        if len(out) > len(lines):
            out = out[: len(lines)]
        while len(out) < len(lines):
            out.append([(lines[len(out)], PLAIN)])
        return out, lexer.name

