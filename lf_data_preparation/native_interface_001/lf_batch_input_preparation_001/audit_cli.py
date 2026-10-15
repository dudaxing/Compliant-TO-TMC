"""Run the real preparation CLI once and record NPZ file-open/load events."""
import json
import os
from pathlib import Path
import runpy
import sys

import numpy as np

events = dict(npz_read_opens=[], numpy_load_calls=[])


def audit(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0]))
        mode = args[1]
        if path.suffix.lower() == '.npz' and isinstance(mode, str) and 'r' in mode:
            events['npz_read_opens'].append(str(path.resolve()))


original_load = np.load


def observed_load(file, *args, **kwargs):
    events['numpy_load_calls'].append(str(Path(file).resolve()) if isinstance(file, (str, os.PathLike)) else type(file).__name__)
    return original_load(file, *args, **kwargs)


sys.addaudithook(audit)
np.load = observed_load
journal, cli, *arguments = sys.argv[1:]
sys.argv = [cli, *arguments]
try:
    runpy.run_path(cli, run_name='__main__')
finally:
    events['scope'] = 'CLI-only NPZ read-open audit and numpy.load calls, including byte-buffer decodes; no universal mechanics hooks'
    Path(journal).write_text(json.dumps(events, indent=2) + '\n', encoding='utf-8')
