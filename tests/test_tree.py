from codeappendix.tree import render


def test_render_tree():
    lines = render("demo", ["src/app.py", "src/util/io.py", "main.py", "README.md"])
    assert lines == [
        "demo/",
        "├── src/",
        "│   ├── util/",
        "│   │   └── io.py",
        "│   └── app.py",
        "├── main.py",
        "└── README.md",
    ]


def test_empty_tree():
    assert render("demo", []) == ["demo/"]
