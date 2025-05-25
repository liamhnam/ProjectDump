import os
import sys
from pathlib import Path
import fnmatch

MAX_FILE_SIZE = 100 * 1024 * 1024   # 100 MB

def detect_project_tech(project_path):
    """Tự động phát hiện công nghệ dự án dựa trên các file đặc trưng, hỗ trợ glob"""
    tech_indicators = {
        'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', '*.py', '*.ipynb'],
        'javascript': ['package.json', '*.js'],
        'typescript': ['tsconfig.json', '*.ts'],
        'react': ['*.jsx', '*.tsx', 'react.config.js'],
        'vue': ['vue.config.js', '*.vue'],
        'svelte': ['svelte.config.js', '*.svelte'],
        'nextjs': ['next.config.js', 'pages/**/*.js', 'pages/**/*.jsx', 'pages/**/*.ts', 'pages/**/*.tsx'],
        'nuxt': ['nuxt.config.js'],
        'angular': ['angular.json', 'main.ts'],

        'flutter': ['pubspec.yaml', '*.dart'],
        'android': ['build.gradle', 'AndroidManifest.xml'],
        'ios': ['*.xcodeproj', '*.xcworkspace'],

        'java': ['pom.xml', '*.java'],
        'kotlin': ['*.kt'],
        'csharp': ['*.csproj', 'Program.cs'],
        'php': ['composer.json'],
        'ruby': ['Gemfile'],
        'go': ['go.mod'],
        'rust': ['Cargo.toml'],
        'elixir': ['mix.exs'],
        'dart': ['pubspec.yaml'],
        'r': ['*.R', '*.Rproj'],
        'scala': ['build.sbt'],
        'docker': ['Dockerfile'],
        'kubernetes': ['k8s/', 'helm/'],
        'terraform': ['*.tf'],
        'ansible': ['ansible.cfg'],
        'github_actions': ['.github/workflows/'],
        'gitlab_ci': ['.gitlab-ci.yml'],
        'circleci': ['.circleci/config.yml'],
        'deno': ['deno.json'],
        'bun': ['bun.lockb'],
        'c': ['*.c', '*.h'],
        'cpp': ['*.cpp', '*.hpp']
    }

    detected_techs = set()

    for root, dirs, files in os.walk(project_path):
        rel_root = os.path.relpath(root, project_path)
        for tech, patterns in tech_indicators.items():
            for pattern in patterns:
                if "**" in pattern or "*" in pattern:
                    full_path = os.path.join(rel_root, '').replace("\\", "/")
                    for file in files:
                        file_path = os.path.join(full_path, file)
                        if fnmatch.fnmatchcase(file_path, pattern):
                            detected_techs.add(tech)
                else:
                    for file in files:
                        if file.lower() == pattern.lower():
                            detected_techs.add(tech)

        # Extra logic: add implied techs
        if 'nextjs' in detected_techs:
            detected_techs.update(['react', 'javascript', 'typescript'])
        if 'nuxt' in detected_techs:
            detected_techs.update(['vue', 'javascript', 'typescript'])

    return sorted(detected_techs)


def get_extensions_by_tech(techs):
    tech_extensions = {
        # Python & Data Science
        'python': ['.py', '.pyx', '.pyi'],
        'jupyter': ['.ipynb'],
        'r': ['.r', '.R', '.Rmd', '.Rproj'],

        # JavaScript & Frontend
        'javascript': ['.js', '.jsx', '.mjs', '.cjs'],
        'typescript': ['.ts', '.tsx'],
        'react': ['.jsx', '.tsx', '.js', '.ts'],
        'vue': ['.vue', '.js', '.ts'],
        'svelte': ['.svelte'],
        'angular': ['.ts', '.js', '.html', '.scss'],
        'nextjs': ['.js', '.jsx', '.ts', '.tsx'],
        'nuxt': ['.vue', '.js', '.ts'],

        # Mobile
        'flutter': ['.dart'],
        'android': ['.java', '.kt', '.xml'],
        'ios': ['.swift', '.m', '.mm', '.h', '.xib', '.storyboard'],

        # Backend & Dev
        'java': ['.java', '.kt'],
        'kotlin': ['.kt', '.kts'],
        'csharp': ['.cs', '.vb'],
        'php': ['.php'],
        'ruby': ['.rb', '.erb'],
        'go': ['.go'],
        'rust': ['.rs'],
        'elixir': ['.ex', '.exs'],
        'dart': ['.dart'],
        'scala': ['.scala', '.sc'],
        'cpp': ['.cpp', '.hpp'],
        'c': ['.c', '.h'],

        # Infrastructure
        'docker': ['Dockerfile', '.dockerignore'],
        'kubernetes': ['.yaml', '.yml'],
        'terraform': ['.tf', '.tf.json'],
        'ansible': ['.yml', '.yaml'],

        # CI/CD
        'github_actions': ['.yml'],
        'gitlab_ci': ['.yml'],
        'circleci': ['.yml'],

        # Runtime Environments
        'nodejs': ['.js', '.mjs', '.cjs'],
        'bun': ['.js', '.ts', '.jsx', '.tsx'],
        'deno': ['.ts', '.tsx', '.js'],

        # Config
        'json': ['.json'],
        'yaml': ['.yml', '.yaml'],
        'toml': ['.toml'],
        'xml': ['.xml'],
    }


    extensions = set()
    for tech in techs:
        if tech in tech_extensions:
            extensions.update(tech_extensions[tech])
    
    return extensions

def get_essential_files():
    """Chỉ lấy các file mã nguồn, không lấy config"""
    return set()  # Không lấy file config

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
    'db', 'database', 'sqlite', 'sessions', 'flask_session', 'instance',
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
    """Kiểm tra xem đường dẫn có nên bị loại trừ không"""
    path_parts = Path(path).parts
    return any(part.lower() in exclude_dirs for part in path_parts)

def should_exclude_file(filename, exclude_files):
    """Kiểm tra xem file có nên bị loại trừ không"""
    filename_lower = filename.lower()
    return any(
        filename_lower == pattern.lower() or 
        (pattern.startswith('*.') and filename_lower.endswith(pattern[2:].lower()))
        for pattern in exclude_files
    )

def generate_directory_tree(project_path, exclude_dirs):
    """Tạo cây thư mục đầy đủ - thư mục thư viện chỉ hiển thị tên, không hiển thị file bên trong"""
    tree_lines = []
    project_name = os.path.basename(project_path.rstrip(os.sep))
    tree_lines.append(f"{project_name}/")
    
    def add_directory_content(current_path, prefix=""):
        try:
            items = sorted(os.listdir(current_path))
            dirs = [item for item in items if os.path.isdir(os.path.join(current_path, item))]
            files = [item for item in items if os.path.isfile(os.path.join(current_path, item))]
            
            # Hiển thị thư mục
            for i, dirname in enumerate(dirs):
                is_last_dir = (i == len(dirs) - 1) and len(files) == 0
                
                # Kiểm tra xem có phải thư mục thư viện không
                if dirname.lower() in exclude_dirs:
                    tree_lines.append(f"{prefix}{'└── ' if is_last_dir else '├── '}{dirname}/")
                    continue  # Không duyệt vào bên trong thư mục thư viện
                else:
                    tree_lines.append(f"{prefix}{'└── ' if is_last_dir else '├── '}{dirname}/")
                    next_prefix = prefix + ("    " if is_last_dir else "│   ")
                    add_directory_content(os.path.join(current_path, dirname), next_prefix)
            
            # Hiển thị files
            for i, filename in enumerate(files):
                is_last = i == len(files) - 1
                tree_lines.append(f"{prefix}{'└── ' if is_last else '├── '}{filename}")
                
        except PermissionError:
            tree_lines.append(f"{prefix}├── [Permission Denied]")
    
    add_directory_content(project_path)
    return "\n".join(tree_lines)

def aggregate_code(project_path):
    """Hàm chính để tổng hợp code"""
    if not os.path.isdir(project_path):
        print(f"❌ Lỗi: Thư mục '{project_path}' không tồn tại!")
        return False

    print(f"🔍 Đang phân tích dự án tại: {project_path}")
    print("🔍 Đang quét thư mục...")

    # Phát hiện công nghệ
    detected_techs = detect_project_tech(project_path)
    if detected_techs:
        print(f"🛠️  Phát hiện công nghệ: {', '.join(detected_techs)}")
    else:
        print("⚠️  Không phát hiện được công nghệ cụ thể, sử dụng tất cả file code")

    # Lấy extensions cần thiết
    target_extensions = get_extensions_by_tech(detected_techs)
    essential_files = get_essential_files()
    exclude_dirs, exclude_files = get_exclude_patterns()

    print(f"📁 Extensions sẽ được bao gồm: {', '.join(sorted(target_extensions))}")

    # Tạo nội dung tổng hợp
    content_lines = []

    # Header
    content_lines.append("# TỔNG HỢP MÃ NGUỒN DỰ ÁN")
    content_lines.append("# " + "="*50)
    content_lines.append(f"# Đường dẫn: {project_path}")
    content_lines.append(f"# Công nghệ phát hiện: {', '.join(detected_techs) if detected_techs else 'Không xác định'}")
    content_lines.append("# " + "="*50)
    content_lines.append("")

    print("📁 Đang tạo cây thư mục...")
    # Cây thư mục
    content_lines.append("## CẤU TRÚC THƯ MỤC")
    content_lines.append("```")
    content_lines.append(generate_directory_tree(project_path, exclude_dirs))
    content_lines.append("```")
    content_lines.append("")

    # Tổng hợp files
    print("📄 Đang xử lý các tệp...")
    content_lines.append("## NỘI DUNG CÁC FILE")
    content_lines.append("")

    file_count = 0
    total_size = 0

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if not should_exclude_path(os.path.join(root, d), exclude_dirs)]

        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_path)

            if should_exclude_path(rel_path, exclude_dirs) or should_exclude_file(file, exclude_files):
                continue

            file_ext = Path(file).suffix.lower()
            is_target_ext = file_ext in target_extensions
            if not is_target_ext:
                continue

            try:
                file_size = os.path.getsize(file_path)
                if file_size > MAX_FILE_SIZE:
                    print(f"⚠️  Bỏ qua {rel_path} (kích thước {file_size:,} byte > giới hạn {MAX_FILE_SIZE:,} byte)")
                    continue

                print(f"  📝 Xử lý: {rel_path}")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read()

                content_lines.append(f"### {rel_path}")
                content_lines.append("```" + (file_ext[1:] if file_ext else ""))
                content_lines.append(file_content)
                content_lines.append("```")
                content_lines.append("")

                file_count += 1
                total_size += len(file_content)

            except Exception as e:
                content_lines.append(f"### {rel_path}")
                content_lines.append(f"```\n# Lỗi đọc file: {str(e)}\n```")
                content_lines.append("")

    # Ghi file kết quả
    output_path = os.path.join(project_path, "source_dump.txt")
    final_content = '\n'.join(content_lines)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

        with open(output_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        print("")
        print(f"✅ Thành công! Đã tạo file: {output_path}")
        print("")
        print(f"📊 Thống kê:")
        print(f"   - Số file đã xử lý: {file_count}")
        print(f"   - Kích thước file đầu ra: {len(final_content):,} ký tự (~{total_size // 1024} KB)")
        print(f"   - Tổng số dòng: {line_count:,} dòng")
        return True

    except Exception as e:
        print(f"❌ Lỗi ghi file: {str(e)}")
        return False


def main():
    """Hàm main"""
    print("🚀 PROJECTDUMP")
    print("="*40)
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = input("📂 Nhập đường dẫn thư mục dự án: ").strip()
        if not project_path:
            project_path = os.getcwd()
    
    # Chuẩn hóa đường dẫn
    project_path = os.path.abspath(project_path)
    
    # Thực hiện tổng hợp
    success = aggregate_code(project_path)
    
    if success:
        print("\n🎉 Hoàn thành! File source_dump.txt đã sẵn sàng.")
    else:
        print("\n💥 Có lỗi xảy ra trong quá trình xử lý.")
        sys.exit(1)

if __name__ == "__main__":
    main()