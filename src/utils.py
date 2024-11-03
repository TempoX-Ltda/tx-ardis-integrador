from pathlib import Path


def get_version():
    current_dir = Path(__file__).parent

    version_file = current_dir / "version"

    return version_file.read_text().strip()
