# HW1 submission

**Name:** Bakdaulet
**Student ID:** 23068143
**Group:**
**Repository:** https://github.com/bakhyttuly/css4007-hw1

## AI tool disclosure

State which AI tools you used and for what. Expected and fine; undisclosed use
is not.

> I used Claude (Anthropic's AI assistant) throughout this assignment: to implement the `TODO` functions in `sublab_easy/registration_bot.py`, `sublab_medium/correct_kazakh.py` and `sublab_hard/tokenizer_forensics.py`; to debug real API errors I hit while running them (OpenRouter's free-tier rate limiting on `gemma`, an insufficient-credit error on `qwen` tied to its default max-output-token request, and `qwen` repeatedly exhausting its token budget on hidden reasoning before producing an answer); and to draft and later simplify the written answers below, based on the real token counts, costs and model outputs produced by running the actual scripts against OpenAI and OpenRouter. All tables and numbers in this document come from real runs, not estimates.

---

## Sublab Easy — the registration bot and its bill

**How I laid the catalogue out inside the system prompt, and why:**

>

**My turn 5 (Kazakh or Russian):**

>

### Run 1 — OpenAI, `gpt-5.6-luna`

| Turn | Input tokens | Output tokens | Cost $ |
|---|---|---|---|
| 1 | 752 | 461 | 0.000704 |
| 2 | 1077 | 97 | 0.000332 |
| 3 | 1160 | 69 | 0.000315 |
| 4 | 1248 | 37 | 0.000294 |
| 5 | 1313 | 338 | 0.000668 |
| **total** | | | 0.002312 |

### Run 2 — OpenRouter, `google/gemma-4-26b-a4b-it:free`

| Turn | Input tokens | Output tokens | Cost $ |
|---|---|---|---|
| 1 | 846 | 406 | 0.000000 |
| 2 | 1271 | 75 | 0.000000 |
| 3 | 1364 | 79 | 0.000000 |
| 4 | 1459 | 8 | 0.000000 |
| 5 | 1492 | 589 | 0.000000 |
| **total** | | | 0.000000 |

### Turn 4, verbatim

The turn where you asked for CSS-4090, which does not exist. Paste both replies
exactly as they came back — do not tidy them.

**OpenAI:**

```
I can't add CSS-4090 Quantum Machine Learning because it does not exist in the provided Narxoz University 2026-FALL course catalogue.
```

**OpenRouter:**

```
No such course exists in the catalogue.
```

### Written answers

**1. The two providers used almost identical code. What actually changed, and
what did not?**

> Only the `base_url` changed. `openrouter_client()` creates the same `OpenAI` client but with `base_url=https://openrouter.ai/api/v1` and the OpenRouter key. Everything else stays the same: the message format, the `chat()` call, and reading `choices[0].message.content` and `usage`. OpenRouter uses the same API format as OpenAI, so one URL and one key were enough to reach a different model.

**2. Why did the input token count climb on every turn when your questions
stayed roughly the same length? Use the numbers from your own table. What
happens to the bill at fifty turns?**

> The API does not remember anything, so every call sends the system prompt plus the whole conversation so far. That is why input tokens grew 752 → 1077 → 1160 → 1248 → 1313 even though my questions were short. Each new turn pays again for all the old turns, so the total cost grows much faster than the number of turns. At fifty turns the last call alone would be several thousand input tokens, and the whole conversation would cost far more than fifty separate questions.

**3. Turn 4: did the bot refuse, or did it invent CSS-4090?** If it refused, what
in your system prompt held the line? If it invented, what did it make up —
credits, a room, an instructor?

> Both refused. OpenAI: "I can't add CSS-4090 Quantum Machine Learning because it does not exist in the provided ... catalogue." OpenRouter: "No such course exists in the catalogue." What held the line was the last paragraph of my system prompt: the catalogue is the full list of courses, and the bot must refuse and never invent a course, credits, schedule or instructor. Neither bot made anything up.

**4. Where else was either bot wrong?** Turn 2 asks for two courses that meet at
the same hour; two courses in the catalogue are full. Did the bots notice?

> Yes. `gpt-5.6-luna` showed some of its internal reasoning text in the turn 1 answer. `gemma` in turn 1 offered `ECN-2101` as a course I could take, but I have already completed it, and the rules say you cannot register for a completed course.

---

## Sublab Medium — one task, six models

Paste the per-model summary printed by `correct_kazakh.py`:

| Model | Exact | Failed | Tokens | Cost $ |
|---|---|---|---|---|
| google/gemma-4-26b-a4b-it:free | 5 | 0 | 2028 | 0.00000 |
| qwen/qwen3.8-27b | 0 | 8 | 0 | 0.00000 |
| deepseek/deepseek-v4-flash-0731 | 8 | 0 | 14669 | 0.00385 |
| gpt-5.6-luna | 7 | 0 | 4173 | 0.00358 |
| gpt-5.6-terra | 6 | 0 | 3013 | 0.02188 |
| gpt-5.6-sol | 6 | 0 | 2771 | 0.04743 |

### Which error types did each model repair?

Rows are error labels, columns are models. Write "yes", "no" or "partial".

| Error type | gemma | qwen | deepseek | luna | terra | sol |
|---|---|---|---|---|---|---|
| kaz_to_rus | partial | no | yes | partial | partial | partial |
| latin_homoglyph | partial | no | yes | yes | yes | yes |
| drop_hyphen | no | no | yes | yes | yes | yes |
| join_words | yes | no | yes | yes | partial | yes |
| double_letter | yes | no | yes | yes | yes | yes |

**The `latin_homoglyph` row: what happened?** Describe what you observed. The
explanation is Sublab Harder's job, not this one's.

> deepseek, luna, terra and sol fixed both homoglyph sentences (KZ-03, KZ-08). gemma fixed only one of them. qwen fixed nothing, but qwen failed every sentence, so this says nothing specific about homoglyphs. So most models still recovered the right Kazakh word even though the Latin letters look identical to the Cyrillic ones.

**Where a model returned good Kazakh that was not identical to the original,
say so here.** Exact match is not correctness.

> KZ-01 (`kaz_to_rus`): deepseek and luna matched the original exactly, but gemma, terra and sol did not. Three different models giving a different answer to the same sentence suggests a valid alternative correction (different word choice) rather than broken Kazakh. I would need to read their outputs in `outputs/corrections.json` to be sure.

**Cheapest model that was good enough, and why:**

> deepseek: 8/8 exact for $0.00385. luna was slightly cheaper ($0.00358) but got 7/8, and free gemma got only 5/8. terra and sol cost 6–13 times more than deepseek and got only 6/8, so the most expensive models were not the most accurate here.

---

## Sublab Harder — open the tokenizer

### A. What a language costs

**`cl100k_base`:**

| Language | Tokens | Chars | Tok/char | × English | $ per 1,000 sentences |
|---|---|---|---|---|---|
| kk | 200 | 263 | 0.760 | 3.75 | 0.1666 |
| ru | 129 | 277 | 0.466 | 2.30 | 0.1076 |
| en | 59 | 291 | 0.203 | 1.00 | 0.0492 |

**`o200k_base`:**

| Language | Tokens | Chars | Tok/char | × English | $ per 1,000 sentences |
|---|---|---|---|---|---|
| kk | 84 | 263 | 0.319 | 1.58 | 0.0699 |
| ru | 74 | 277 | 0.267 | 1.32 | 0.0616 |
| en | 59 | 291 | 0.203 | 1.00 | 0.0492 |

### B. What a homoglyph does

One row per `latin_homoglyph` sentence in the dataset. Paste the actual decoded
token strings around the divergence point, not a description of them.

| Sentence id | Foreign char (index, name) | Tokens correct | Tokens corrupted | Δ | Diverges at |
|---|---|---|---|---|---|
| KZ-03 | 0 'A' LATIN CAPITAL LETTER A; 2 'a' LATIN SMALL LETTER A; 5 't' LATIN SMALL LETTER T | 16 | 20 | +4 | 0 |
| KZ-08 | 1 'o' LATIN SMALL LETTER O; 3 'a' LATIN SMALL LETTER A; 9 'T' LATIN CAPITAL LETTER T | 21 | 24 | +3 | 1 |

**Token pieces around the divergence:**

```
KZ-03
correct  : ['А', 'лая', 'қ', 'тарға', ' ақша']
corrupted: ['A', 'л', 'a', 'я', 'қ']

KZ-08
correct  : ['Д', 'он', 'аль', 'д', ' Т', 'рамп']
corrupted: ['Д', 'o', 'н', 'a', 'л', 'ль']
```

### C. Did it get better?

| Language | cl100k_base | o200k_base | Change |
|---|---|---|---|
| kk | 0.760 | 0.319 | −58.0% |
| ru | 0.466 | 0.267 | −42.7% |
| en | 0.203 | 0.203 | 0% |

### Written answers

**1. What is the Kazakh tax?** The ratio against English in both encodings, the
dollar figure from A, and how much it changed between the two tokenizers.

> In `cl100k_base` Kazakh costs 3.75× English (0.760 vs 0.203 tokens per character), or $0.1666 vs $0.0492 per 1,000 sentences. In `o200k_base` it is 1.58× ($0.0699 vs $0.0492). The newer tokenizer cut the Kazakh cost by 58%, but Kazakh is still about 58% more expensive than English.

**2. Why did the models repair `kaz_to_rus` but struggle with
`latin_homoglyph`?** Both are single-letter substitutions and both look almost
identical on screen. Use your token streams from B as the evidence. Say what the
model actually received in each case.

> The model does not see letters, it sees tokens. In `kaz_to_rus` the letters stay Cyrillic, so the text becomes normal-looking Cyrillic tokens, like a common misspelling the model has seen many times. In `latin_homoglyph` a Latin letter replaces a Cyrillic one, which is a different byte and so a different token. The token streams split right away: KZ-03 differs at token 0 (`['A', 'л', 'a', 'я', 'қ']` vs `['А', 'лая', 'қ', 'тарға', ' ақша']`), KZ-08 at token 1. The model receives rare, broken pieces instead of a familiar word.

**3. Name one thing this measurement does not explain about your Sublab Medium
results.** You measured OpenAI's tokenizers; three of your six models were not
OpenAI's. What follows, and what would you have to do to close the gap?

> I only measured OpenAI's tokenizers, but gemma, qwen and deepseek use their own tokenizers. So these numbers do not explain their results, for example why gemma fixed only one homoglyph sentence. To check, I would need to load each model's own tokenizer and repeat the same measurements.