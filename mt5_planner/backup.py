from datetime import datetime
from pathlib import Path
from shutil import copy2


def run_backup(files: list[str], output_dir: str = "backups") -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = Path(output_dir) / stamp
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for file_name in files:
        source = Path(file_name)
        if source.exists() and source.is_file():
            destination = target_dir / source.name
            copy2(source, destination)
            copied.append(str(destination))
    lines = [f"backup_dir: {target_dir}", f"copied: {len(copied)}"]
    lines.extend(copied)
    return "\n".join(lines)
