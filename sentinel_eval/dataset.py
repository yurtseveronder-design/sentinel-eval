import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATASET = Path(__file__).resolve().parent.parent / "data" / "prompts.jsonl"


@dataclass(frozen=True)
class Sample:
    id: str
    label: str  # "attack" or "benign"
    category: str
    text: str


def load(path=DEFAULT_DATASET):
    samples = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if raw.get("label") not in ("attack", "benign"):
            raise ValueError(f"line {number}: label must be 'attack' or 'benign'")
        samples.append(Sample(raw["id"], raw["label"], raw["category"], raw["text"]))
    ids = [s.id for s in samples]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate sample ids")
    return samples
