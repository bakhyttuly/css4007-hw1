"""Sublab Easy - a course-registration chatbot, and the bill it runs up."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

CATALOGUE = Path(__file__).resolve().parent.parent / "data" / "courses.json"

RATES_PER_MTOK = {
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.6-terra": (2.00, 12.00),
    "gpt-5.6-sol": (5.00, 30.00),
    "google/gemma-4-26b-a4b-it:free": (0.00, 0.00),
    "qwen/qwen3.8-27b": (0.45, 3.20),
    "deepseek/deepseek-v4-flash-0731": (0.14, 0.28),
}


def load_catalogue() -> dict:
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))


def openai_client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env.")
    return OpenAI(api_key=key)


def openrouter_client() -> OpenAI:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Copy .env.example to .env.")
    return OpenAI(api_key=key, base_url=OPENROUTER_BASE_URL)


def client_for(via: str) -> OpenAI:
    if via == "openai":
        return openai_client()
    if via == "openrouter":
        return openrouter_client()
    raise ValueError('via must be "openai" or "openrouter", got ' + repr(via))


def build_system_prompt(catalogue: dict) -> str:
    rules = catalogue["rules"]
    student = catalogue["student"]

    course_lines = []
    for c in catalogue["courses"]:
        prereqs = ", ".join(c["prerequisites"]) if c["prerequisites"] else "none"
        schedule = "; ".join(
            "%s %s-%s" % (s["day"], s["start"], s["end"]) for s in c["schedule"]
        )
        seats_left = c["seats_total"] - c["seats_taken"]
        course_lines.append(
            "- %s %s | %d credits | prerequisites: %s | meets: %s | "
            "seats: %d/%d taken (%d remaining) | instructor: %s"
            % (c["code"], c["title"], c["credits"], prereqs, schedule,
               c["seats_taken"], c["seats_total"], seats_left, c["instructor"])
        )

    completed = ", ".join(student["completed"]) if student["completed"] else "none"

    return (
        "You are the course registrar for Narxoz University, term %s.\n"
        "You know ONLY what is written below. You have no other knowledge of "
        "Narxoz, its courses, its instructors, or its rules.\n\n"
        "STUDENT\n"
        "- Student ID: %s\n"
        "- Year: %d\n"
        "- Programme: %s\n"
        "- Already completed (and may not register for again): %s\n\n"
        "REGISTRATION RULES\n"
        "- Maximum credits per term: %d\n"
        "- Minimum credits per term: %d\n"
        "- %s\n"
        "- A student may not register for two courses whose meeting times "
        "overlap on the same day.\n\n"
        "COURSE CATALOGUE (this is the complete list; nothing else exists)\n"
        "%s\n\n"
        "STRICT INSTRUCTION: The catalogue above is the entire set of courses "
        "that exist at this university. If a student asks about a course code, "
        "title, or topic that is NOT in this list, you MUST refuse and say "
        "plainly that no such course exists in the catalogue. Do NOT invent a "
        "course, a credit count, a schedule, an instructor, or a seat count "
        "under any circumstances, even if the student insists or the name "
        "sounds plausible. Only use the facts given above - never guess."
        % (catalogue["term"], student["student_id"], student["year"],
           student["programme"], completed, rules["max_credits"],
           rules["min_credits"], rules["note"], "\n".join(course_lines))
    )


def chat(messages: list[dict], model: str = "gpt-5.6-luna",
         via: str = "openai") -> dict:
    client = client_for(via)
    response = client.chat.completions.create(model=model, messages=messages,
                                              max_tokens=4096)
    text = response.choices[0].message.content
    usage = response.usage
    return {
        "text": text,
        "input_tokens": usage.prompt_tokens,
        "output_tokens": usage.completion_tokens,
        "model": model,
    }


def ask_once(prompt: str, model: str = "gpt-5.6-luna",
             via: str = "openai") -> dict:
    return chat([{"role": "user", "content": prompt}], model=model, via=via)


def new_conversation(catalogue: dict) -> list[dict]:
    return [{"role": "system", "content": build_system_prompt(catalogue)}]


def run_turn(history: list[dict], user_text: str, model: str = "gpt-5.6-luna",
             via: str = "openai") -> tuple[list[dict], dict]:
    history = history + [{"role": "user", "content": user_text}]
    reply = chat(history, model=model, via=via)
    history = history + [{"role": "assistant", "content": reply["text"]}]
    return history, reply


def estimate_cost(input_tokens: int, output_tokens: int,
                  rate_in: float, rate_out: float) -> float:
    return (input_tokens / 1_000_000) * rate_in + (output_tokens / 1_000_000) * rate_out


def cost_of(usage: dict) -> float:
    rate_in, rate_out = RATES_PER_MTOK[usage["model"]]
    return estimate_cost(usage["input_tokens"], usage["output_tokens"],
                         rate_in, rate_out)


def conversation_cost(usages: list[dict]) -> float:
    return sum((cost_of(u) for u in usages), 0.0)


SCRIPT = [
    "I am a third-year student. Which courses am I still eligible to register for?",
    "Register me for CSS-4007 and CSS-4102.",
    "How many credits would that be in total, and am I within the limit?",
    "Add CSS-4090 Quantum Machine Learning to my schedule.",
    "Мен үшінші курс студентімін. Мен әлі қандай курстарға тіркеле аламын?",
]


def run_script(model: str, via: str) -> list[dict]:
    history = new_conversation(load_catalogue())
    usages = []

    print("\n===== " + via + " / " + model + " =====")
    for i, user_text in enumerate(SCRIPT, start=1):
        history, usage = run_turn(history, user_text, model=model, via=via)
        usages.append(usage)
        print("\n--- turn %d ---" % i)
        print("you: " + user_text)
        print("bot: " + usage["text"])
        print("     in=%6d  out=%5d  $%.6f"
              % (usage["input_tokens"], usage["output_tokens"], cost_of(usage)))

    print("\n%10s%8s%7s%12s" % ("", "in", "out", "cost"))
    for i, u in enumerate(usages, start=1):
        print("turn %-5d%8d%7d%12.6f"
              % (i, u["input_tokens"], u["output_tokens"], cost_of(u)))
    print("%25s%s" % ("", "-" * 12))
    print("%25s%12.6f" % ("total", conversation_cost(usages)))
    return usages


if __name__ == "__main__":
    if any(t.startswith("TODO") for t in SCRIPT):
        raise SystemExit("Write turn 5 in Kazakh or Russian first.")

    run_script("gpt-5.6-luna", "openai")
    run_script("google/gemma-4-26b-a4b-it:free", "openrouter")