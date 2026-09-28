"""Sublab Harder - why Kazakh costs more, and what a homoglyph does to a word."""

import json
import unicodedata
from pathlib import Path

import tiktoken

DATA = Path(__file__).resolve().parent.parent / "data"
PARALLEL = DATA / "parallel.json"
KAZAKH_ERRORS = DATA / "kazakh_errors.json"

ENCODINGS = ["cl100k_base", "o200k_base"]

LANGS = ["kk", "ru", "en"]


def load_triplets() -> list[dict]:
    return json.loads(PARALLEL.read_text(encoding="utf-8"))["triplets"]


def load_sentences() -> list[dict]:
    return json.loads(KAZAKH_ERRORS.read_text(encoding="utf-8"))["sentences"]


def encode(text: str, encoding_name: str = "o200k_base") -> list[int]:
    return tiktoken.get_encoding(encoding_name).encode(text)


def pieces(ids: list[int], encoding_name: str = "o200k_base") -> list[str]:
    enc = tiktoken.get_encoding(encoding_name)
    return [enc.decode_single_token_bytes(i).decode("utf-8", errors="replace")
            for i in ids]


def tokens_per_char(text: str, ids: list[int]) -> float:
    if not text:
        return 0.0
    return len(ids) / len(text)


def first_divergence(a: list[int], b: list[int]) -> int | None:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    if len(a) != len(b):
        return n
    return None


def foreign_chars(text: str) -> list[tuple[int, str, str]]:
    result = []
    for idx, ch in enumerate(text):
        if not ch.isalpha():
            continue
        try:
            name = unicodedata.name(ch)
        except ValueError:
            name = ""
        if "CYRILLIC" not in name:
            result.append((idx, ch, name))
    return result


def language_table(encoding_name: str) -> dict[str, dict]:
    triplets = load_triplets()
    table = {}
    for lang in LANGS:
        total_tokens = 0
        total_chars = 0
        for triplet in triplets:
            text = triplet[lang]
            total_tokens += len(encode(text, encoding_name))
            total_chars += len(text)
        table[lang] = {
            "tokens": total_tokens,
            "chars": total_chars,
            "tok_per_char": (total_tokens / total_chars) if total_chars else 0.0,
        }
    return table


def cost_per_thousand(tok_per_char: float, chars: int,
                      rate_in: float = 5.00) -> float:
    tokens_per_sentence = tok_per_char * chars
    cost_per_sentence = (tokens_per_sentence / 1_000_000) * rate_in
    return cost_per_sentence * 1000


def homoglyph_report(corrupted: str, correct: str,
                     encoding_name: str = "o200k_base") -> dict:
    ids_correct = encode(correct, encoding_name)
    ids_corrupted = encode(corrupted, encoding_name)
    return {
        "foreign": foreign_chars(corrupted),
        "tokens_correct": len(ids_correct),
        "tokens_corrupted": len(ids_corrupted),
        "delta": len(ids_corrupted) - len(ids_correct),
        "diverge_at": first_divergence(ids_correct, ids_corrupted),
        "pieces_correct": pieces(ids_correct, encoding_name),
        "pieces_corrupted": pieces(ids_corrupted, encoding_name),
    }


def show_homoglyphs(encoding_name: str = "o200k_base") -> None:
    rows = [r for r in load_sentences() if "latin_homoglyph" in r["errors"]]
    if not rows:
        print("  no latin_homoglyph rows in the dataset")
        return
    for row in rows:
        rep = homoglyph_report(row["corrupted"], row["correct"], encoding_name)
        print("\n  [%s]  %+d tokens (%d -> %d), diverging at index %s"
              % (row["id"], rep["delta"], rep["tokens_correct"],
                 rep["tokens_corrupted"], rep["diverge_at"]))
        for idx, ch, name in rep["foreign"]:
            print("    char %d is %r - %s" % (idx, ch, name))
        d = rep["diverge_at"] or 0
        print("    correct  : %s" % rep["pieces_correct"][max(0, d - 1):d + 5])
        print("    corrupted: %s" % rep["pieces_corrupted"][max(0, d - 1):d + 5])


if __name__ == "__main__":
    print("=== A. the same six meanings, three languages, two tokenizers ===")
    for enc_name in ENCODINGS:
        table = language_table(enc_name)
        print("\n  %s" % enc_name)
        print("    %-4s %8s %8s %12s" % ("lang", "tokens", "chars", "tok/char"))
        for lang in LANGS:
            row = table[lang]
            print("    %-4s %8d %8d %12.3f"
                  % (lang, row["tokens"], row["chars"], row["tok_per_char"]))
        base = table["en"]["tok_per_char"]
        for lang in LANGS:
            print("    %s costs %.2fx English"
                  % (lang, table[lang]["tok_per_char"] / base))

    print("\n=== B. what a Latin homoglyph does to the token stream ===")
    show_homoglyphs("o200k_base")

    print("\n=== C. did the newer tokenizer narrow the gap? ===")
    old, new = (language_table(e) for e in ENCODINGS)
    for lang in LANGS:
        print("  %s: %.3f -> %.3f tok/char"
              % (lang, old[lang]["tok_per_char"], new[lang]["tok_per_char"]))
    print("\n  Now answer question 2 in SUBMISSION.md, with these numbers in hand.")