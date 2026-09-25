from __future__ import annotations

from codeappendix.config import Config, apply
from codeappendix.scanner import (
    R_BINARY,
    R_BOILERPLATE,
    R_DEPENDENCY,
    R_EXCLUDED,
    R_GENERATED,
    R_GITIGNORE,
    R_HIDDEN,
    R_MINIFIED,
    R_NOT_SOURCE,
    R_TOO_LARGE,
    R_VENDORED,
    scan,
)


def rels(result):
    return [c.rel for c in result.files]


def reasons(result):
    return dict(result.skipped)


def test_takes_source_and_skips_the_rest(make_project):
    root = make_project({
        "main.py": "print('hi')\n",
        "README.md": "# demo\n",
        "logo.png": b"\x89PNG\r\n",
        "data.json": "{}",
        "node_modules/lib/index.js": "x",
        "build/out.js": "x",
        ".venv/lib/site.py": "x",
    })
    result = scan(root, Config())
    assert rels(result) == ["main.py"]
    skipped = reasons(result)
    assert skipped["README.md"] == R_NOT_SOURCE
    assert skipped["logo.png"] == R_BINARY
    assert skipped["node_modules/"] == R_DEPENDENCY
    assert skipped["build/"] == R_DEPENDENCY
    assert skipped[".venv/"] == R_DEPENDENCY


def test_lib_and_packages_folders_are_kept(make_project):
    # The old tool dropped these, which emptied every Flutter project.
    root = make_project({
        "lib/main.dart": "void main() {}\n",
        "packages/core/index.ts": "export {}\n",
    })
    assert rels(scan(root, Config())) == ["lib/main.dart", "packages/core/index.ts"]


def test_virtualenv_with_any_name_is_skipped(make_project):
    root = make_project({"app.py": "x=1\n", "myenv/pyvenv.cfg": "home = /usr\n", "myenv/lib/x.py": "x"})
    result = scan(root, Config())
    assert rels(result) == ["app.py"]
    assert reasons(result)["myenv/"] == R_DEPENDENCY


def test_nested_gitignore_and_negation(make_project):
    root = make_project({
        ".gitignore": "secret.py\n*.gen.ts\n",
        "secret.py": "x",
        "src/a.gen.ts": "x",
        "src/.gitignore": "!a.gen.ts\nlocal/\n",
        "src/local/b.ts": "x",
        "src/c.ts": "x",
    })
    result = scan(root, Config())
    assert rels(result) == ["src/a.gen.ts", "src/c.ts"]
    skipped = reasons(result)
    assert skipped["secret.py"] == R_GITIGNORE
    assert skipped["src/local/"] == R_GITIGNORE


def test_gitignore_can_be_disabled(make_project):
    root = make_project({".gitignore": "b.py\n", "a.py": "x", "b.py": "x"})
    assert rels(scan(root, apply(Config(), {"use_gitignore": False}))) == ["a.py", "b.py"]


def test_include_overrides_defaults_but_not_exclude(make_project):
    root = make_project({
        "main.py": "x",
        "config/app.json": "{}",
        "build/generated/Api.java": "class Api {}",
        "tests/test_main.py": "x",
    })
    cfg = apply(Config(), {
        "include": ["config/*.json", "build/generated/*.java"],
        "exclude": ["tests/"],
    })
    result = scan(root, cfg)
    assert rels(result) == ["build/generated/Api.java", "config/app.json", "main.py"]
    assert reasons(result)["tests/"] == R_EXCLUDED


def test_include_star_pattern_does_not_open_dependency_folders(make_project):
    root = make_project({"a.json": "{}", "node_modules/x/b.json": "{}"})
    result = scan(root, apply(Config(), {"include": ["*.json"]}))
    assert rels(result) == ["a.json"]


def test_only_restricts(make_project):
    root = make_project({"src/a.py": "x", "scripts/b.py": "x"})
    assert rels(scan(root, apply(Config(), {"only": ["src/**"]}))) == ["src/a.py"]


def test_order_moves_files_first(make_project):
    root = make_project({"a.py": "x", "b.py": "x", "src/main.py": "x", "src/util.py": "x"})
    result = scan(root, apply(Config(), {"order": ["src/main.py", "b.py"]}))
    assert rels(result) == ["src/main.py", "b.py", "src/util.py", "a.py"]


def test_tree_order_folders_first_and_natural(make_project):
    root = make_project({"file10.py": "x", "file2.py": "x", "z/a.py": "x", "a/z.py": "x"})
    assert rels(scan(root, Config())) == ["a/z.py", "z/a.py", "file2.py", "file10.py"]


def test_generated_minified_and_vendored_names(make_project):
    root = make_project({
        "lib/model.dart": "class A {}",
        "lib/model.g.dart": "part of 'model.dart';",
        "static/app.min.js": "x",
        "static/jquery-3.7.1.js": "x",
        "gradlew.bat": "@echo off",
    })
    result = scan(root, Config())
    assert rels(result) == ["lib/model.dart"]
    skipped = reasons(result)
    assert skipped["lib/model.g.dart"] == R_GENERATED
    assert skipped["static/app.min.js"] == R_MINIFIED
    assert skipped["static/jquery-3.7.1.js"] == R_VENDORED
    assert skipped["gradlew.bat"] == R_GENERATED


def test_hidden_folders_skipped(make_project):
    root = make_project({"main.go": "package main", ".github/scripts/ci.sh": "echo"})
    result = scan(root, Config())
    assert rels(result) == ["main.go"]
    assert reasons(result)[".github/"] == R_HIDDEN


def test_flutter_platform_folders_are_boilerplate(make_project):
    root = make_project({
        "pubspec.yaml": "name: app\ndependencies:\n  flutter:\n    sdk: flutter\n",
        "lib/main.dart": "void main() {}",
        "android/app/src/main/kotlin/MainActivity.kt": "class MainActivity",
        "windows/runner/main.cpp": "int main() {}",
    })
    result = scan(root, Config())
    assert rels(result) == ["lib/main.dart"]
    assert reasons(result)["android/"] == R_BOILERPLATE
    assert reasons(result)["windows/"] == R_BOILERPLATE


def test_plain_dart_package_keeps_platform_named_folders(make_project):
    root = make_project({"pubspec.yaml": "name: tool\n", "web/main.dart": "void main() {}"})
    assert rels(scan(root, Config())) == ["web/main.dart"]


def test_react_native_platform_folders(make_project):
    root = make_project({
        "package.json": '{"dependencies": {"react-native": "0.74.0"}}',
        "App.tsx": "export default 1",
        "ios/AppDelegate.mm": "x",
    })
    result = scan(root, Config())
    assert rels(result) == ["App.tsx"]
    assert reasons(result)["ios/"] == R_BOILERPLATE


def test_default_excludes_off_scans_everything(make_project):
    root = make_project({"a.py": "x", "build/b.py": "x", ".tools/c.py": "x"})
    cfg = apply(Config(), {"default_excludes": False})
    assert rels(scan(root, cfg)) == [".tools/c.py", "build/b.py", "a.py"]


def test_too_large(make_project):
    root = make_project({"big.py": "x = 1\n" * 400, "small.py": "x"})
    result = scan(root, apply(Config(), {"max_file_kb": 1}))
    assert rels(result) == ["small.py"]
    assert reasons(result)["big.py"] == R_TOO_LARGE


def test_output_file_inside_project_is_ignored(make_project):
    root = make_project({"a.py": "x", "out.py": "x"})
    result = scan(root, Config(), output=root / "out.py")
    assert rels(result) == ["a.py"]


def test_special_filenames(make_project):
    root = make_project({"Dockerfile": "FROM python", "Makefile": "all:", "CMakeLists.txt": "project(x)"})
    assert rels(scan(root, Config())) == ["CMakeLists.txt", "Dockerfile", "Makefile"]
