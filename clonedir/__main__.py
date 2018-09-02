from typing import Dict, Optional, Tuple, Union

import argparse
import os
from pathlib import Path

import numpy as np


def str_to_bool(x):
    return x.lower() == 'true'


parser = argparse.ArgumentParser()

parser.add_argument('source', help='the source directory to use')
parser.add_argument('clones', nargs='+', help='the destination directory to use')
parser.add_argument('--use_checksum', action='store', type=str_to_bool, dest='use_checksum',
                    required=False, default=True)

CS_Key = Union[Tuple[int, int], str]


def checksum(path: Path) -> CS_Key:
    # the checksum key is subject to change, currently returns the sum and length of the
    if path.is_dir():
        return 'dir'
    b = np.frombuffer(path.read_bytes(), dtype=np.uint8)
    return len(b), int(b.sum(dtype=int))


def main(args=None):
    args = parser.parse_args(args)

    src_path = Path(args.source)
    master_files: Dict[Path, Optional[CS_Key]] = {Path(f): None for f in src_path.rglob('*')}

    if args.use_checksum:
        print('calculating checksums')
        for i, f in enumerate(master_files):
            master_files[f] = checksum(f)
            print(f'{i+1} of {len(master_files)}')
        print('checksums calculated')

    for clone_dir in args.clones:
        for path, cs in master_files.items():
            clone_file = Path(clone_dir) / path.relative_to(args.source)
            copy = True
            if clone_file.exists() and cs and checksum(clone_file) == cs:
                copy = False

            if copy:
                print(f'doing: {path} -> {clone_file}...', end='')
                if path.is_dir():
                    clone_file.mkdir(parents=True, exist_ok=True)
                else:
                    clone_file.write_bytes(path.read_bytes())
                print('done!')

        for path in Path(clone_dir).rglob('*'):
            path = Path(path)
            source_file = args.source / path.relative_to(clone_dir)
            if source_file not in master_files:
                print(f'doing del {path}...', end='')
                if path.is_dir():
                    path.rmdir()
                else:
                    os.remove(path.absolute())
                print('done!')


if __name__ == '__main__':
    main()
