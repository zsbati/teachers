import os

# Directories and files to ignore
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'env', 'migrations', 'staticfiles', '.idea', '.vscode', 'node_modules'}
IGNORE_FILES = {'.DS_Store', 'Thumbs.db'}

def generate_tree(directory, max_depth=3, indent="", current_depth=0):
    if current_depth > max_depth:
        return
    entries = sorted(os.listdir(directory))
    entries = [e for e in entries if e not in IGNORE_FILES]
    dirs = [e for e in entries if os.path.isdir(os.path.join(directory, e)) and e not in IGNORE_DIRS]
    files = [e for e in entries if os.path.isfile(os.path.join(directory, e)) and e not in IGNORE_FILES]

    for idx, dirname in enumerate(dirs):
        is_last = (idx == len(dirs) - 1 and not files)
        print(f"{indent}{'└── ' if is_last else '├── '}{dirname}/")
        generate_tree(os.path.join(directory, dirname), max_depth, indent + ("    " if is_last else "│   "), current_depth + 1)

    for idx, filename in enumerate(files):
        is_last = (idx == len(files) - 1)
        print(f"{indent}{'└── ' if is_last else '├── '}{filename}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print(os.path.basename(project_root) + "/")
    generate_tree(project_root, max_depth=3)