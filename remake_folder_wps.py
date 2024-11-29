import os
import os.path as osp
from pathlib import Path
import shutil
import json
def remake_folder_wps(root, save):
    save = Path(save)
    root = Path(root)
    files = root.rglob('Label.txt')
    for file in files:
        images = file.parent.glob('*.jpg')
        images = list(images)
        f = open(file, 'r', encoding='utf-8')
        lines = f.readlines()
        f.close()
        is_valid = False
        for line in lines:
            line = line.strip()
            lb = line.split('\t')[1]
            lb = eval(lb)
            if len(lb) > 0:
                is_valid=True
                break
        if not is_valid:
            continue
        if len(lines) < len(images):
            continue
        if len(images) == 0:
            continue
        print(f'line: {len(lines)}, image: {len(images)}')
        dirname = file.parent.stem
        tard = save.joinpath(dirname)
        # tard.mkdir(parents=True, exist_ok=True)
        print(tard)
        shutil.copytree(file.parent.parent, tard)
if __name__ == '__main__':
    root = r'wps\download'
    save = r'wps\download2'
    remake_folder_wps(root, save)