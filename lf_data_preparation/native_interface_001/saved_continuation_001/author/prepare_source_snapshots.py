"""Copy ordinary baseline source bytes to an isolated candidate; no HF imports."""
from pathlib import Path

ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
EXTERNAL = Path(__file__).resolve().parent
NAMES = (
    "hf_repo/src/hf_eval/split_displacement.py",
    "hf_repo/src/hf_eval/native_mean.py",
    "hf_repo/src/hf_eval/native_evaluate.py",
    "hf_repo/src/hf_eval/native_response.py",
    "hf_repo/scripts/solve_native_mean.py",
    "hf_repo/scripts/evaluate_native.py",
)
for name in NAMES:
    raw = (ROOT/name).read_bytes()
    for subdirectory in ("baseline", "candidate"):
        path = EXTERNAL/subdirectory/name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
print("six baseline and candidate source snapshots copied; no candidate imports")
