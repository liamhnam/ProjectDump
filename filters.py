from pathlib import Path

def get_essential_files():
    return set()

def get_exclude_patterns():
    exclude_dirs = {
    # Dependencies & environments
    'node_modules', 'vendor', 'venv', 'env', '.venv', '.env', '.mypy_cache', '.ruff_cache', '.pytest_cache', '__pycache__', 
    '.cache', 'pip-wheel-metadata', 'site-packages', 'deps', 'packages', '.tox',

    # Build artifacts
    'dist', 'build', 'target', 'out', 'bin', 'obj', '.eggs', 'lib', 'lib64', 'generated',

    # CMake build
    'cmake-build-debug', 'cmake-build-debug-visual-studio', 'cmake-build-release-visual-studio',

    # Framework build folders
    '.next', '.nuxt', '.angular', 'coverage', '.turbo', '.vercel', '.expo', '.parcel-cache',

    # Version control & IDE tools
    '.git', '.svn', '.hg', '.idea', '.vscode', '.vs', '.history', '.vscode-test',

    # Temp & OS folders
    'temp', 'tmp', '.tmp', '.DS_Store', '__MACOSX', 'Thumbs.db', 'System Volume Information',

    # CI/CD & Docker volumes
    '.github', '.gitlab', '.circleci', '.docker', 'logs', 'log', 'docker', 'containers',

    # Database & sessions
    'db', 'database', 'sqlite', 'sessions', 'flask_session', 'instance'
    }

    exclude_files = {
        # Logs
        '*.log', '*.log.*', '*.out',

        # Package manager lock files
        'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'composer.lock', 'poetry.lock', 'Cargo.lock',

        # Compiled/intermediate binaries
        '*.pyc', '*.pyo', '*.pyd', '*.class', '*.o', '*.so', '*.dll', '*.exe', '*.dylib', '*.a',

        # Media files
        '*.jpg', '*.jpeg', '*.png', '*.gif', '*.svg', '*.ico', '*.webp',
        '*.mp3', '*.wav', '*.mp4', '*.avi', '*.mov', '*.mkv', '*.flac', '*.ogg',

        # Fonts
        '*.ttf', '*.otf', '*.woff', '*.woff2',

        # Archives & compressed
        '*.zip', '*.tar', '*.gz', '*.rar', '*.7z', '*.bz2', '*.xz', '*.lz', '*.lzma',

        # Office / documents
        '*.pdf', '*.docx', '*.doc', '*.ppt', '*.pptx', '*.xls', '*.xlsx', '*.csv',

        # OS/system files
        '.DS_Store', 'Thumbs.db', 'desktop.ini', 'ehthumbs.db', 'Icon\r',

        # Misc config/cache
        '*.env', '*.env.*', '*.ini', '*.toml', '*.bak', '*.swp', '*.swo',
    }

    
    return exclude_dirs, exclude_files

def should_exclude_path(path, exclude_dirs):
    return any(part.lower() in exclude_dirs for part in Path(path).parts)

def should_exclude_file(filename, exclude_files):
    filename_lower = filename.lower()
    return any(
        filename_lower == pattern.lower() or 
        (pattern.startswith('*.') and filename_lower.endswith(pattern[2:].lower()))
        for pattern in exclude_files
    )
