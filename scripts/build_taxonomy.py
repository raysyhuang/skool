"""Rebuild the vendored Marble Skill Taxonomy subset in app/seed/taxonomy/.

The upstream dataset (https://github.com/lauramionel/os-taxonomy) covers ages
4-16 across 8 subjects and is ~4 MB. Skool only has two kids, so we vendor the
slice that matters — ages 4-10 — and drop the fields we never read.

Usage:
    git clone https://github.com/lauramionel/os-taxonomy /tmp/os-taxonomy
    python scripts/build_taxonomy.py /tmp/os-taxonomy

Licensing: the upstream database is ODbL 1.0, the authored content CC BY-SA
4.0. See NOTICE at the repo root — anything we redistribute keeps that lineage.
"""
import json
import os
import sys

AGE_MIN = 4
AGE_MAX = 10

# Prerequisite edges only matter for subjects that have a playable topic spine.
GRAPH_SUBJECTS = {"Mathematics", "English"}

TOPIC_FIELDS = (
    "id", "type", "subject", "domain", "name", "description",
    "ageRangeStart", "ageRangeEnd", "centrality", "evidence", "assessmentPrompt",
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, os.pardir, "app", "seed", "taxonomy")


def _load(src: str, name: str, key: str) -> list:
    with open(os.path.join(src, "data", name), encoding="utf-8") as f:
        return json.load(f)[key]


def build(src: str) -> None:
    topics = _load(src, "topics.json", "topics")
    deps = _load(src, "dependencies.json", "dependencies")

    with open(os.path.join(OUT_DIR, "topic_modes.json"), encoding="utf-8") as f:
        modes = json.load(f)

    # topic id -> generator mode, flattened across subjects. A topic mapped to
    # two modes would silently take whichever won the loop, so refuse it.
    mode_by_id: dict[str, str] = {}
    clashes: list[str] = []
    for subject_key in ("math", "english"):
        for mode, topic_ids in modes[subject_key].items():
            for tid in topic_ids:
                if tid in mode_by_id:
                    clashes.append(f"{tid}: {mode_by_id[tid]} and {mode}")
                mode_by_id[tid] = mode
    if clashes:
        raise SystemExit("topic_modes.json maps a topic to two modes:\n  " + "\n  ".join(clashes))

    kept = [
        t for t in topics
        if t["ageRangeStart"] <= AGE_MAX and t["ageRangeEnd"] >= AGE_MIN
    ]
    kept_ids = {t["id"] for t in kept}

    missing = sorted(set(mode_by_id) - kept_ids)
    if missing:
        raise SystemExit(
            f"topic_modes.json references {len(missing)} unknown topic ids: {missing}"
        )

    out_topics = []
    for t in sorted(kept, key=lambda x: x["id"]):
        row = {k: t[k] for k in TOPIC_FIELDS}
        row["questionMode"] = mode_by_id.get(t["id"])
        out_topics.append(row)

    graph_ids = {t["id"] for t in kept if t["subject"] in GRAPH_SUBJECTS}
    out_deps = sorted(
        (
            d for d in deps
            if d["topicId"] in graph_ids and d["prerequisiteId"] in graph_ids
        ),
        key=lambda d: (d["topicId"], d["prerequisiteId"]),
    )

    _write("topics.json", {
        "source": "https://github.com/lauramionel/os-taxonomy",
        "license": "ODbL-1.0 (database) / CC-BY-SA-4.0 (content)",
        "ageRange": [AGE_MIN, AGE_MAX],
        "topicCount": len(out_topics),
        "playableCount": sum(1 for t in out_topics if t["questionMode"]),
        "topics": out_topics,
    })
    _write("dependencies.json", {
        "source": "https://github.com/lauramionel/os-taxonomy",
        "license": "ODbL-1.0",
        "note": "topicId depends on prerequisiteId. Reverse the edge to get 'unlocks'.",
        "subjects": sorted(GRAPH_SUBJECTS),
        "edgeCount": len(out_deps),
        "dependencies": out_deps,
    })

    print(f"topics.json      {len(out_topics):5d} topics "
          f"({sum(1 for t in out_topics if t['questionMode'])} playable)")
    print(f"dependencies.json {len(out_deps):4d} edges")


def _write(name: str, payload: dict) -> None:
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    build(sys.argv[1])
