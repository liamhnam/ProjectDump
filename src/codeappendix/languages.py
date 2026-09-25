"""Which files count as source code, and what language each one is.

The table maps a file extension (or an exact file name) to a display name and
the Pygments lexer alias used for syntax highlighting. Only files matching this
table are included by default; everything else (JSON, YAML, Markdown, images…)
must be added explicitly with ``include``.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

# extension -> (display name, pygments alias). A ``None`` alias means "let
# Pygments guess from the file name and content" (used for ambiguous
# extensions such as ``.m``, which can be Objective-C or MATLAB).
EXTENSIONS: Dict[str, Tuple[str, Optional[str]]] = {
    # Python & data
    ".py": ("Python", "python"),
    ".pyw": ("Python", "python"),
    ".pyi": ("Python", "python"),
    ".pyx": ("Cython", "cython"),
    ".ipynb": ("Jupyter Notebook", "python"),
    ".r": ("R", "r"),
    ".rmd": ("R Markdown", "md"),
    ".jl": ("Julia", "julia"),
    ".sql": ("SQL", "sql"),
    # Web
    ".js": ("JavaScript", "javascript"),
    ".mjs": ("JavaScript", "javascript"),
    ".cjs": ("JavaScript", "javascript"),
    ".jsx": ("JavaScript (JSX)", "jsx"),
    ".ts": ("TypeScript", "typescript"),
    ".mts": ("TypeScript", "typescript"),
    ".cts": ("TypeScript", "typescript"),
    ".tsx": ("TypeScript (TSX)", "tsx"),
    ".vue": ("Vue", "vue"),
    ".svelte": ("Svelte", "html"),
    ".astro": ("Astro", "html"),
    ".html": ("HTML", "html"),
    ".htm": ("HTML", "html"),
    ".css": ("CSS", "css"),
    ".scss": ("SCSS", "scss"),
    ".sass": ("Sass", "sass"),
    ".less": ("Less", "less"),
    ".php": ("PHP", "html+php"),
    ".twig": ("Twig", "html+twig"),
    ".ejs": ("EJS", "html"),
    ".hbs": ("Handlebars", "html+handlebars"),
    ".pug": ("Pug", "pug"),
    ".jsp": ("JSP", "jsp"),
    ".cshtml": ("Razor", "html"),
    ".razor": ("Razor", "html"),
    ".erb": ("ERB", "erb"),
    # JVM
    ".java": ("Java", "java"),
    ".kt": ("Kotlin", "kotlin"),
    ".kts": ("Kotlin", "kotlin"),
    ".scala": ("Scala", "scala"),
    ".groovy": ("Groovy", "groovy"),
    ".gradle": ("Gradle", "groovy"),
    ".clj": ("Clojure", "clojure"),
    # C family & systems
    ".c": ("C", "c"),
    ".h": ("C/C++ Header", "cpp"),
    ".cpp": ("C++", "cpp"),
    ".cc": ("C++", "cpp"),
    ".cxx": ("C++", "cpp"),
    ".hpp": ("C++ Header", "cpp"),
    ".hh": ("C++ Header", "cpp"),
    ".hxx": ("C++ Header", "cpp"),
    ".ino": ("Arduino", "arduino"),
    ".cs": ("C#", "csharp"),
    ".vb": ("Visual Basic", "vbnet"),
    ".fs": ("F#", "fsharp"),
    ".xaml": ("XAML", "xml"),
    ".go": ("Go", "go"),
    ".rs": ("Rust", "rust"),
    ".zig": ("Zig", "zig"),
    ".swift": ("Swift", "swift"),
    ".m": ("Objective-C / MATLAB", None),
    ".mm": ("Objective-C++", "objective-c++"),
    ".dart": ("Dart", "dart"),
    ".asm": ("Assembly", "nasm"),
    ".s": ("Assembly", "gas"),
    ".v": ("Verilog", "verilog"),
    ".sv": ("SystemVerilog", "systemverilog"),
    ".vhd": ("VHDL", "vhdl"),
    ".vhdl": ("VHDL", "vhdl"),
    ".pas": ("Pascal", "delphi"),
    ".dpr": ("Pascal", "delphi"),
    ".f90": ("Fortran", "fortran"),
    ".sol": ("Solidity", "solidity"),
    # Scripting & functional
    ".rb": ("Ruby", "ruby"),
    ".lua": ("Lua", "lua"),
    ".pl": ("Perl", "perl"),
    ".pm": ("Perl", "perl"),
    ".ex": ("Elixir", "elixir"),
    ".exs": ("Elixir", "elixir"),
    ".erl": ("Erlang", "erlang"),
    ".hs": ("Haskell", "haskell"),
    ".ml": ("OCaml", "ocaml"),
    ".elm": ("Elm", "elm"),
    ".nim": ("Nim", "nim"),
    ".sh": ("Shell", "bash"),
    ".bash": ("Shell", "bash"),
    ".zsh": ("Shell", "zsh"),
    ".ps1": ("PowerShell", "powershell"),
    ".bat": ("Batch", "batch"),
    ".cmd": ("Batch", "batch"),
    # Interfaces
    ".proto": ("Protocol Buffers", "protobuf"),
    ".graphql": ("GraphQL", "graphql"),
    ".gql": ("GraphQL", "graphql"),
}

# Files without an extension (or with a fixed name) that are still source code.
FILENAMES: Dict[str, Tuple[str, Optional[str]]] = {
    "dockerfile": ("Dockerfile", "docker"),
    "makefile": ("Makefile", "make"),
    "cmakelists.txt": ("CMake", "cmake"),
}

# Extensions that are never source code, whatever the user asks: binary data
# that cannot be rendered as text in a document.
BINARY_EXTENSIONS = frozenset(
    """
    .png .jpg .jpeg .gif .bmp .ico .webp .tif .tiff .psd .svgz
    .mp3 .wav .ogg .flac .aac .m4a .mp4 .mkv .avi .mov .webm
    .ttf .otf .woff .woff2 .eot
    .zip .tar .gz .tgz .bz2 .xz .7z .rar .jar .war .apk .aab .ipa
    .exe .dll .so .dylib .a .lib .o .obj .class .pyc .pyo .pyd .wasm
    .pdf .doc .docx .xls .xlsx .ppt .pptx .odt .ods
    .db .sqlite .sqlite3 .mdb .bin .dat .pkl .npy .npz .h5 .onnx .pt .pth
    """.split()
)


def lookup(name: str) -> Optional[Tuple[str, Optional[str]]]:
    """Return ``(display name, lexer alias)`` for a file name, or ``None``."""
    lower = name.lower()
    if lower in FILENAMES:
        return FILENAMES[lower]
    if lower.startswith("dockerfile."):  # Dockerfile.dev, Dockerfile.prod
        return FILENAMES["dockerfile"]
    dot = lower.rfind(".")
    if dot <= 0:
        return None
    return EXTENSIONS.get(lower[dot:])


def is_binary_name(name: str) -> bool:
    lower = name.lower()
    dot = lower.rfind(".")
    return dot > 0 and lower[dot:] in BINARY_EXTENSIONS
