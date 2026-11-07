#!/usr/bin/env python3
"""PortGoose morphogenesis worker.

Reads sandbox-input.json, applies a *whitelisted ordered stack* of geometric
mutations and writes sandbox.json. No user-supplied code is executed.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = ("grow", "fork", "twist", "mirror", "prune", "bloom", "ripple", "thicken")
MAX_OPS = 18
MAX_SEGMENTS = 500
MAX_BLOOMS = 150


def number(value: float) -> float:
    return round(float(value), 6)


def segment(a: list[float], b: list[float], width: float, tip: bool = True, generation: int = 0) -> dict:
    return {"a": [number(a[0]), number(a[1])], "b": [number(b[0]), number(b[1])],
            "width": number(width), "tip": tip, "generation": generation}


def rotate(dx: float, dy: float, angle: float) -> tuple[float, float]:
    return (dx * math.cos(angle) - dy * math.sin(angle),
            dx * math.sin(angle) + dy * math.cos(angle))


def validate(data: dict) -> tuple[list[dict], int, str]:
    if not isinstance(data, dict):
        raise ValueError("sandbox-input.json must be an object.")
    operations = data.get("operations", [])
    seed = data.get("seed", 4)
    revision = data.get("revision", "default")
    if not isinstance(operations, list) or len(operations) > MAX_OPS:
        raise ValueError("operations must be a list of no more than 18 elements.")
    if type(seed) is not int or not 0 <= seed <= 999999:
        raise ValueError("seed must be an integer from 0 to 999999.")
    if not isinstance(revision, str) or len(revision) > 100:
        raise ValueError("revision must be a short string.")
    seen: set[str] = set()
    for op in operations:
        if not isinstance(op, dict) or op.get("type") not in ALLOWED:
            raise ValueError("Unrecognized mutation operation.")
        if type(op.get("enabled")) is not bool:
            raise ValueError("Each operation must specify an enabled boolean.")
        identifier = op.get("id")
        if not isinstance(identifier, str) or not 0 < len(identifier) <= 80 or identifier in seen:
            raise ValueError("Operation identifiers must be distinct short strings.")
        seen.add(identifier)
    return operations, seed, revision


def mutate(data: dict) -> dict:
    operations, seed, revision = validate(data)
    segments = [segment([0, -0.92], [0, -0.30], .045, True)]
    blooms: list[dict] = []
    history: list[dict] = []

    def map_all(fn) -> None:
        for seg in segments:
            seg["a"] = [number(v) for v in fn(*seg["a"])]
            seg["b"] = [number(v) for v in fn(*seg["b"])]
        for bloom in blooms:
            bloom["center"] = [number(v) for v in fn(*bloom["center"])]

    for index, op in enumerate(operations):
        if not op["enabled"]:
            history.append({"type": op["type"], "enabled": False, "segments": len(segments), "blooms": len(blooms)})
            continue
        kind = op["type"]
        tips = [s for s in segments if s["tip"]]
        if kind == "grow":
            generated = []
            for i, s in enumerate(tips):
                if len(segments) + len(generated) >= MAX_SEGMENTS:
                    break
                dx, dy = s["b"][0] - s["a"][0], s["b"][1] - s["a"][1]
                length = math.hypot(dx, dy)
                if length < 1e-6:
                    continue
                angle = .16 * math.sin(seed * .9 + index * 3.7 + i * 2.31)
                vx, vy = rotate(dx / length, dy / length, angle)
                distance = max(.13, min(.65, length * 0.84))
                end = [s["b"][0] + vx * distance, s["b"][1] + vy * distance]
                generated.append(segment(s["b"], end, s["width"] * .83, True, s["generation"] + 1))
                s["tip"] = False
            segments.extend(generated)
        elif kind == "fork":
            generated = []
            for i, s in enumerate(tips):
                if len(segments) + len(generated) + 2 > MAX_SEGMENTS:
                    break
                dx, dy = s["b"][0] - s["a"][0], s["b"][1] - s["a"][1]
                length = max(.01, math.hypot(dx, dy))
                distance = max(.12, min(.54, length * .79))
                sway = .07 * math.sin(seed + i * 4.3 + index * 2)
                for direction in (-1, 1):
                    vx, vy = rotate(dx / length, dy / length, direction * .56 + sway)
                    end = [s["b"][0] + vx * distance, s["b"][1] + vy * distance]
                    generated.append(segment(s["b"], end, s["width"] * .74, True, s["generation"] + 1))
                s["tip"] = False
            segments.extend(generated)
        elif kind == "twist":
            def twist(x, y):
                t = .32 * (y + 1.2)
                return rotate(x, y, t)
            map_all(twist)
        elif kind == "mirror":
            originals = list(segments)
            for s in originals:
                if len(segments) >= MAX_SEGMENTS:
                    break
                segments.append(segment([-s["a"][0], s["a"][1]], [-s["b"][0], s["b"][1]],
                                        s["width"], s["tip"], s["generation"]))
            original_blooms = list(blooms)
            for flower in original_blooms:
                if len(blooms) >= MAX_BLOOMS:
                    break
                blooms.append({"center": [number(-flower["center"][0]), flower["center"][1]],
                               "radius": flower["radius"], "petals": flower["petals"]})
        elif kind == "prune":
            if len(tips) > 1:
                remove = {id(s) for i, s in enumerate(tips) if i % 3 == 1}
                segments[:] = [s for s in segments if id(s) not in remove]
            elif tips:
                s = tips[0]
                s["b"] = [number(s["a"][k] + (s["b"][k] - s["a"][k]) * .64) for k in range(2)]
        elif kind == "bloom":
            for i, s in enumerate(tips):
                if len(blooms) >= MAX_BLOOMS:
                    break
                blooms.append({"center": s["b"][:],
                               "radius": number(.065 + .007 * (i % 4)),
                               "petals": 5 + (i + seed) % 3})
        elif kind == "ripple":
            map_all(lambda x, y: (x + .14 * math.sin(y * 6.2 + seed * .11),
                                  y + .075 * math.sin(x * 9 + seed * .15)))
        elif kind == "thicken":
            for s in segments:
                s["width"] = number(min(.22, s["width"] * 1.7))
            for flower in blooms:
                flower["radius"] = number(min(.17, flower["radius"] * 1.26))
        history.append({"type": kind, "enabled": True,
                        "segments": len(segments), "blooms": len(blooms)})

    coords = [p for s in segments for p in (s["a"], s["b"])]
    coords += [b["center"] for b in blooms]
    bounds = {"xmin": number(min(p[0] for p in coords)), "xmax": number(max(p[0] for p in coords)),
              "ymin": number(min(p[1] for p in coords)), "ymax": number(max(p[1] for p in coords))}
    return {
        "schema": 2, "status": "ok", "revision": revision, "seed": seed,
        "operations": operations, "segments": segments, "blooms": blooms,
        "history": history, "bounds": bounds,
        "stats": {"segments": len(segments), "blooms": len(blooms),
                  "active": sum(1 for op in operations if op["enabled"])},
    }


def main() -> None:
    data = json.loads((ROOT / "sandbox-input.json").read_text(encoding="utf-8"))
    result = mutate(data)
    result["updated_at"] = datetime.now(timezone.utc).isoformat()
    (ROOT / "sandbox.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print("Processed", result["revision"], result["stats"])


if __name__ == "__main__":
    main()
