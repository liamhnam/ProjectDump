import os
import sys
from pathlib import Path
import fnmatch
from typing import Set, List, Dict

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


def detect_project_tech(project_path: str) -> List[str]:
    """Tự động phát hiện công nghệ dự án dựa trên các file đặc trưng, hỗ trợ glob"""
    tech_indicators: Dict[str, List[str]] = {
        "python": [
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
            "Pipfile",
            "*.py",
            "*.ipynb",
        ],
        "javascript": ["package.json", "*.js"],
        "typescript": ["tsconfig.json", "*.ts"],
        "react": ["*.jsx", "*.tsx", "react.config.js"],
        "vue": ["vue.config.js", "*.vue"],
        "svelte": ["svelte.config.js", "*.svelte"],
        "nextjs": [
            "next.config.js",
            "pages/**/*.js",
            "pages/**/*.jsx",
            "pages/**/*.ts",
            "pages/**/*.tsx",
        ],
        "nuxt": ["nuxt.config.js"],
        "angular": ["angular.json", "main.ts"],
        "flutter": ["pubspec.yaml", "*.dart"],
        "android": ["build.gradle", "AndroidManifest.xml"],
        "ios": ["*.xcodeproj", "*.xcworkspace"],
        "java": ["pom.xml", "*.java"],
        "kotlin": ["*.kt"],
        "csharp": ["*.csproj", "Program.cs"],
        "php": ["composer.json"],
        "ruby": ["Gemfile"],
        "go": ["go.mod"],
        "rust": ["Cargo.toml"],
        "elixir": ["mix.exs"],
        "dart": ["pubspec.yaml"],
        "r": ["*.R", "*.Rproj"],
        "scala": ["build.sbt"],
        "docker": ["Dockerfile"],
        "kubernetes": ["k8s/", "helm/"],
        "terraform": ["*.tf"],
        "ansible": ["ansible.cfg"],
        "github_actions": [".github/workflows/"],
        "gitlab_ci": [".gitlab-ci.yml"],
        "circleci": [".circleci/config.yml"],
        "deno": ["deno.json"],
        "bun": ["bun.lockb"],
        "c": ["*.c", "*.h"],
        "cpp": ["*.cpp", "*.hpp"]
    }

    detected_techs: Set[str] = set()

    for root, _, files in os.walk(project_path):
        rel_root = os.path.relpath(root, project_path)
        for tech, patterns in tech_indicators.items():
            for pattern in patterns:
                if "**" in pattern or "*" in pattern:
                    full_path = os.path.join(rel_root, "").replace("\\", "/")
                    for file in files:
                        file_path = os.path.join(full_path, file)
                        if fnmatch.fnmatchcase(file_path, pattern):
                            detected_techs.add(tech)
                else:
                    for file in files:
                        if file.lower() == pattern.lower():
                            detected_techs.add(tech)

        # Extra logic: add implied techs
        if "nextjs" in detected_techs:
            detected_techs.update(set(["react", "javascript", "typescript"]))
        if "nuxt" in detected_techs:
            detected_techs.update(set(["vue", "javascript", "typescript"]))

    return sorted(list(detected_techs))


def get_extensions_by_tech(techs: List[str]) -> Set[str]:
    tech_extensions: Dict[str, List[str]] = {
        # Python & Data Science
        "python": [".py", ".pyx", ".pyi"],
        "jupyter": [".ipynb"],
        "r": [".r", ".R", ".Rmd", ".Rproj"],
        # JavaScript & Frontend
        "javascript": [".js", ".jsx", ".mjs", ".cjs"],
        "typescript": [".ts", ".tsx"],
        "react": [".jsx", ".tsx", ".js", ".ts"],
        "vue": [".vue", ".js", ".ts"],
        "svelte": [".svelte"],
        "angular": [".ts", ".js", ".html", ".scss"],
        "nextjs": [".js", ".jsx", ".ts", ".tsx"],
        "nuxt": [".vue", ".js", ".ts"],
        # Mobile
        "flutter": [".dart"],
        "android": [".java", ".kt", ".xml"],
        "ios": [".swift", ".m", ".mm", ".h", ".xib", ".storyboard"],
        # Backend & Dev
        "java": [".java", ".kt"],
        "kotlin": [".kt", ".kts"],
        "csharp": [".cs", ".vb"],
        "php": [".php"],
        "ruby": [".rb", ".erb"],
        "go": [".go"],
        "rust": [".rs"],
        "elixir": [".ex", ".exs"],
        "dart": [".dart"],
        "scala": [".scala", ".sc"],

        # Systems Programming
        "cpp": [".cpp", ".hpp"],
        "c": [".c", ".h"],

        # Infrastructure
        "docker": ["Dockerfile", ".dockerignore"],
        "kubernetes": [".yaml", ".yml"],
        "terraform": [".tf", ".tf.json"],
        "ansible": [".yml", ".yaml"],
        # CI/CD
        "github_actions": [".yml"],
        "gitlab_ci": [".yml"],
        "circleci": [".yml"],
        # Runtime Environments
        "nodejs": [".js", ".mjs", ".cjs"],
        "bun": [".js", ".ts", ".jsx", ".tsx"],
        "deno": [".ts", ".tsx", ".js"],
        # Config
        "json": [".json"],
        "yaml": [".yml", ".yaml"],
        "toml": [".toml"],
        "xml": [".xml"],
    }

    extensions: Set[str] = set()
    for tech in techs:
        if tech in tech_extensions:
            extensions.update(set(tech_extensions[tech]))

    return extensions


def get_essential_files() -> Set[str]:
    """Chỉ lấy các file mã nguồn, không lấy config"""
    return set()  # Không lấy file config


def get_exclude_patterns() -> Dict[str, Set[str]]:
    exclude_dirs: Set[str] = {
        # Dependencies & environments
        "node_modules",
        "vendor",
        "venv",
        "env",
        ".venv",
        ".env",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "__pycache__",
        ".cache",
        "pip-wheel-metadata",
        "site-packages",
        "deps",
        "packages",
        ".tox",
        # Build artifacts
        "dist",
        "build",
        "target",
        "out",
        "bin",
        "obj",
        ".eggs",
        "lib",
        "lib64",
        "generated",
        
        # CMake build
        "cmake-build-debug",
        "cmake-build-debug-visual-studio",
        "cmake-build-release-visual-studio",

        # Framework build folders
        ".next",
        ".nuxt",
        ".angular",
        "coverage",
        ".turbo",
        ".vercel",
        ".expo",
        ".parcel-cache",
        # Version control & IDE tools
        ".git",
        ".svn",
        ".hg",
        ".idea",
        ".vscode",
        ".vs",
        ".history",
        ".vscode-test",
        # Temp & OS folders
        "temp",
        "tmp",
        ".tmp",
        ".DS_Store",
        "__MACOSX",
        "Thumbs.db",
        "System Volume Information",
        # CI/CD & Docker volumes
        ".github",
        ".gitlab",
        ".circleci",
        ".docker",
        "logs",
        "log",
        "docker",
        "containers",
        # Database & sessions
        "db",
        "database",
        "sqlite",
        "sessions",
        "flask_session",
        "instance",
    }

    exclude_files: Set[str] = {
        # Logs
        "*.log",
        "*.log.*",
        "*.out",
        # Package manager lock files
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "composer.lock",
        "poetry.lock",
        "Cargo.lock",
        # Compiled/intermediate binaries
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*.class",
        "*.o",
        "*.so",
        "*.dll",
        "*.exe",
        "*.dylib",
        "*.a",
        # Media files
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.gif",
        "*.svg",
        "*.ico",
        "*.webp",
        "*.mp3",
        "*.wav",
        "*.mp4",
        "*.avi",
        "*.mov",
        "*.mkv",
        "*.flac",
        "*.ogg",
        # Fonts
        "*.ttf",
        "*.otf",
        "*.woff",
        "*.woff2",
        # Archives & compressed
        "*.zip",
        "*.tar",
        "*.gz",
        "*.rar",
        "*.7z",
        "*.bz2",
        "*.xz",
        "*.lz",
        "*.lzma",
        # Office / documents
        "*.pdf",
        "*.docx",
        "*.doc",
        "*.ppt",
        "*.pptx",
        "*.xls",
        "*.xlsx",
        "*.csv",
        # OS/system files
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
        "ehthumbs.db",
        "Icon\r",
        # Misc config/cache
        "*.env",
        "*.env.*",
        "*.ini",
        "*.toml",
        "*.bak",
        "*.swp",
        "*.swo",
    }

    return {"dirs": exclude_dirs, "files": exclude_files}


def should_exclude_path(path: str, exclude_dirs: Set[str]) -> bool:
    """Check if a path should be excluded based on directory patterns"""
    path_parts = Path(path).parts
    return any(part in exclude_dirs for part in path_parts)


def should_exclude_file(filename: str, exclude_files: set[str]) -> bool:
    filename_lower = filename.lower()

    for pattern in exclude_files:
        pattern = pattern.lower()

        # Nếu pattern là *.ext → so sánh đúng đuôi file
        if pattern.startswith("*.") and filename_lower.endswith(pattern[1:]):
            return True

        # Nếu pattern là tên file cụ thể (vd: package-lock.json)
        if filename_lower == pattern:
            return True

    return False


def generate_directory_tree(
    project_path: str, exclude_dirs: Set[str]
) -> List[str]:
    """Generate a directory tree structure"""
    project_name: str = os.path.basename(project_path.rstrip("/"))
    tree: List[str] = []
    tree.append(project_name)

    def add_directory_content(current_path: str, prefix: str = "") -> None:
        items: List[str] = sorted(os.listdir(current_path))
        dirs: List[str] = []
        files: List[str] = []

        for item in items:
            item_path = os.path.join(current_path, item)
            if os.path.isdir(item_path):
                dirs.append(item)
            elif os.path.isfile(item_path):
                files.append(item)

        # Add directories
        for d in dirs:
            dir_path = os.path.join(current_path, d)
            if not should_exclude_path(dir_path, exclude_dirs):
                dirname = os.path.basename(dir_path)
                tree.append(f"{prefix}├── {dirname}/")
                add_directory_content(dir_path, prefix + "│   ")

        # Add files
        for f in files:
            file_path = os.path.join(current_path, f)
            if not should_exclude_file(f, get_exclude_patterns()["files"]):
                filename = os.path.basename(file_path)
                tree.append(f"{prefix}├── {filename}")

    add_directory_content(project_path)
    return tree


def aggregate_code(
    project_path: str, exclude_dirs: Set[str], exclude_files: Set[str]
) -> str:
    """Aggregate code from all files in the project"""
    code_content: List[str] = []
    code_content.append("# Project Code Summary\n\n")

    def process_file(file_path: str) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    code_content.append(f"\n## {os.path.basename(file_path)}\n")
                    code_content.append("```\n")
                    code_content.append(content)
                    code_content.append("\n```\n")
        except Exception as e:
            code_content.append(f"\n## {os.path.basename(file_path)}\n")
            code_content.append(f"Error reading file: {str(e)}\n")

    def process_directory(current_path: str) -> None:
        try:
            items = sorted(os.listdir(current_path))
            for item in items:
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    if not should_exclude_path(item_path, exclude_dirs):
                        process_directory(item_path)
                elif os.path.isfile(item_path):
                    if not should_exclude_file(item, exclude_files):
                        process_file(item_path)
        except Exception as e:
            code_content.append(
                f"\nError processing directory {current_path}: {str(e)}\n"
            )

    process_directory(project_path)
    return "\n".join(code_content)


def main() -> None:
    """Main function to process the project"""
    if len(sys.argv) != 2:
        print("Usage: python script.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]
    if not os.path.isdir(project_path):
        print(f"Error: Directory '{project_path}' does not exist!")
        sys.exit(1)

    print(f"Analyzing project at: {project_path}")
    print("Scanning directories...")

    # Detect technologies
    detected_techs = detect_project_tech(project_path)
    if detected_techs:
        print(f"Detected technologies: {', '.join(detected_techs)}")
    else:
        print("No specific technologies detected, using all code files")

    # Get extensions and patterns
    target_extensions = get_extensions_by_tech(detected_techs)
    exclude_patterns = get_exclude_patterns()
    exclude_dirs = exclude_patterns["dirs"]
    exclude_files = exclude_patterns["files"]

    print(f"Including extensions: {', '.join(sorted(target_extensions))}")

    # Generate directory tree and code content
    print("Processing project...")
    code_content = aggregate_code(project_path, exclude_dirs, exclude_files)

    # Write output
    output_path = os.path.join(project_path, "source_dump.txt")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        print(f"Success! Created file: {output_path}")
    except Exception as e:
        print(f"Error writing file: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
