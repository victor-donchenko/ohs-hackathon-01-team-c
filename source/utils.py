from pathlib import Path

def get_project_dir():
    return Path.resolve(Path(__file__) / ".." / "..")
