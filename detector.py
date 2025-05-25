import os
import fnmatch

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