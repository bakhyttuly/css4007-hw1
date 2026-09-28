"""Sublab Medium - one Kazakh-correction task, six models."""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sublab_easy.registration_bot import (RATES_PER_MTOK,  # noqa: E402
                                          ask_once, estimate_cost)

DATA = Path(__file__).resolve().parent.parent / "data" / "kazakh_errors.json"

MODELS = [
    ("openrouter", "google/gemma-4-26b-a4b-it:free"),
    ("openrouter", "qwen/qwen3.8-27b"),
    ("openrouter", "deepseek/deepseek-v4-flash-0731"),
    ("openai", "gpt-5.6-luna"),
    ("openai", "gpt-5.6-terra"),
    ("openai", "gpt-5.6-sol"),
]


def load_sentences() -> list[dict]:
    return json.loads(DATA.read_text(encoding="utf-8"))["sentences"]


def build_prompt(corrupted: str) -> str:
    return (
        "The following text is Kazakh, but it has been damaged. It may contain "
        "letters swapped for the wrong alphabet (Cyrillic letters replaced by "
        "visually identical Latin letters), Kazakh-specific letters replaced by "
        "their Russian lookalikes, two words welded together with a missing "
        "space, a missing hyphen, or a doubled letter.\n\n"
        "Text:\n"
        "%s\n\n"
        "Fix the text and reply with EXACTLY this JSON object and nothing else "
        "- no explanation, no markdown fence, no extra text:\n"
        '{"corrected": "...", "changes": ["...", "..."]}\n\n'
        '"corrected" is the fixed Kazakh sentence. "changes" is a short list '
        "of what you changed (e.g. \"replaced Latin c with Cyrillic с\", "
        "\"joined words split apart\")." % corrupted
    )


def parse_response(text: str) -> dict:
    candidate = text.strip()

    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL)
    if fence:
        candidate = fence.group(1).strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    brace_match = re.search(r"\{.*\}", candidate, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("no JSON object found in model response: %r" % text)


def correct_with(model: str, corrupted: str, via: str) -> dict:
    result = ask_once(build_prompt(corrupted), model=model, via=via)
    parsed = parse_response(result["text"])
    return {
        "corrected": parsed["corrected"],
        "changes": parsed["changes"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "model": model,
    }


def score_correction(returned: str, expected: str) -> dict:
    exact = returned == expected
    common = min(len(returned), len(expected))
    mismatches = sum(1 for a, b in zip(returned[:common], expected[:common]) if a != b)
    char_diff = mismatches + abs(len(returned) - len(expected))
    return {"exact": exact, "char_diff": char_diff}


def run_all() -> list[dict]:
    rows = []
    for via, model in MODELS:
        for s in load_sentences():
            try:
                r = correct_with(model, s["corrupted"], via)
            except Exception as exc:
                rows.append({"model": model, "id": s["id"],
                             "errors": s["errors"], "failed": repr(exc)})
                continue
            rate_in, rate_out = RATES_PER_MTOK[model]
            rows.append({
                "model": model,
                "id": s["id"],
                "errors": s["errors"],
                "corrected": r["corrected"],
                "changes": r["changes"],
                **score_correction(r["corrected"], s["correct"]),
                "cost": estimate_cost(r["input_tokens"], r["output_tokens"],
                                      rate_in, rate_out),
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
            })
    return rows


def summarise(rows: list[dict]) -> None:
    print(f"{'model':38}{'exact':>7}{'failed':>8}{'tokens':>9}{'cost $':>10}")
    print("-" * 72)
    for _, model in MODELS:
        mine = [r for r in rows if r["model"] == model]
        exact = sum(1 for r in mine if r.get("exact"))
        failed = sum(1 for r in mine if r.get("failed"))
        toks = sum(r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in mine)
        cost = sum(r.get("cost", 0.0) for r in mine)
        print(f"{model:38}{exact:>7}{failed:>8}{toks:>9}{cost:>10.5f}")


if __name__ == "__main__":
    out = run_all()
    summarise(out)
    dest = Path(__file__).resolve().parent.parent / "outputs"
    dest.mkdir(exist_ok=True)
    (dest / "corrections.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote outputs/corrections.json ({len(out)} rows)")