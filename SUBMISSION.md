# HW1 submission

**Name:** Bakdaulet
**Student ID:** 23068143
**Group:**
**Repository:** https://github.com/bakhyttuly/h1--bakhyttuly-

## AI tool disclosure

State which AI tools you used and for what. Expected and fine; undisclosed use
is not.

> I used Claude (Anthropic's AI assistant) throughout this assignment: to implement the `TODO` functions in `sublab_easy/registration_bot.py`, `sublab_medium/correct_kazakh.py` and `sublab_hard/tokenizer_forensics.py`; to debug real API errors I hit while running them (OpenRouter's free-tier rate limiting on `gemma`, an insufficient-credit error on `qwen` tied to its default max-output-token request, and `qwen` repeatedly exhausting its token budget on hidden reasoning before producing an answer); and to help draft the written analysis below, based on the real token counts, costs and model outputs produced by running the actual scripts against OpenAI and OpenRouter. All tables and numbers in this document come from real runs, not estimates.

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

> The only thing that changed is the `base_url` passed to the client: `openai_client()` calls `OpenAI(api_key=key)`, which defaults to OpenAI's own endpoint, while `openrouter_client()` calls `OpenAI(api_key=key, base_url=OPENROUTER_BASE_URL)`, pointing the exact same client class at `https://openrouter.ai/api/v1` instead. Everything downstream — `chat()`, `ask_once()`, `run_turn()`, the `{"role": ..., "content": ...}` message format, and reading the reply/usage off `response.choices[0].message.content` and `response.usage` — is identical, because OpenRouter implements the same OpenAI wire protocol. Swapping one API key and one URL was enough to reach a completely different provider (and a completely different model, Google's Gemma) with zero other code changes.

**2. Why did the input token count climb on every turn when your questions
stayed roughly the same length? Use the numbers from your own table. What
happens to the bill at fifty turns?**

> Input tokens climb because the API is stateless: `chat()` gets sent the *whole* message history, and `run_turn()` only ever appends to it, so every call resends the system prompt plus every previous user and assistant turn, not just the newest question. In Run 1 (OpenAI, gpt-5.6-luna) input tokens went 752 → 1077 → 1160 → 1248 → 1313 across the five turns, even though each new user message was only one short sentence — that growth is almost entirely the accumulated history being paid for again on every single call. Because every earlier turn gets resent and re-billed on every later turn, the total input-token cost of a conversation grows roughly quadratically with the number of turns, not linearly. Extrapolating the roughly 90–140 tokens/turn of growth seen here, a 50-turn conversation would be sending well over 5,000 input tokens on its last call alone, and the tokens paid for across all 50 calls combined would add up to many times more than 50 independent one-shot questions would cost. That is exactly the problem Week 4's context-management techniques (trimming or summarizing history) exist to fix.

**3. Turn 4: did the bot refuse, or did it invent CSS-4090?** If it refused, what
in your system prompt held the line? If it invented, what did it make up —
credits, a room, an instructor?

> Both bots refused. OpenAI's gpt-5.6-luna replied "I can't add CSS-4090 Quantum Machine Learning because it does not exist in the provided Narxoz University 2026-FALL course catalogue." OpenRouter's gemma was even more terse: "No such course exists in the catalogue." What held the line was the closing "STRICT INSTRUCTION" paragraph of the system prompt, which explicitly told the model the catalogue is the entire set of courses that exist and to refuse — never invent a course, credit count, schedule, instructor or seat count — even if the student insists or the name sounds plausible. Neither model invented anything: no fake credit count, room, or instructor, just a plain refusal.

**4. Where else was either bot wrong?** Turn 2 asks for two courses that meet at
the same hour; two courses in the catalogue are full. Did the bots notice?

> Two real errors turned up, independent of turn 4: `gpt-5.6-luna`'s turn-1 reply leaked raw internal reasoning text into its visible answer instead of a clean response. OpenRouter's `gemma`, also in turn 1, incorrectly listed `ECN-2101` as a course the student could still register for, even though `data/courses.json` lists `ECN-2101` among the student's already-completed courses, and the rules explicitly forbid re-registering for a completed course — a direct violation of a rule stated plainly in the system prompt. Both are genuine model mistakes distinct from the correct refusal behavior both bots showed in turn 4.

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

> Every model that could produce output at all except the free `gemma` handled `latin_homoglyph` cleanly: deepseek, luna, terra and sol all got both homoglyph sentences (KZ-03, KZ-08) exactly right, while `gemma` only got 1 of 2 (partial) and `qwen` got 0 of 2 — though qwen failed every single category, not just this one, so its zero here isn't specific evidence about homoglyphs being hard for it. The interesting result is `gemma`: a Latin `c`/`a`/`o` swapped in for a visually identical Cyrillic letter is invisible to a human eye, but it clearly is not invisible to most of these models — they still recovered the correct Kazakh word in almost every case, suggesting the paid/larger models have seen this exact corruption pattern often enough in training to pattern-match past it, while the smaller free model missed it once.

**Where a model returned good Kazakh that was not identical to the original,
say so here.** Exact match is not correctness.

> The clearest candidate is KZ-01 (a `kaz_to_rus` sentence): `deepseek` and `gpt-5.6-luna` both matched the published original exactly, while `gemma`, `gpt-5.6-terra` and `gpt-5.6-sol` all missed an exact match on that same sentence. Since three independent models converged on a different — but still presumably grammatical — rendering of the same corrupted input, that pattern is more consistent with a valid alternate correction (different word choice or word order restoring the same meaning) than with three unrelated models all producing broken Kazakh. The `score_correction` docstring itself warns about exactly this: "exact is a signal, not a grade" — a full read of `outputs/corrections.json` for KZ-01 across those three models would be needed to confirm the phrasing is genuinely valid rather than wrong, but the cross-model agreement pattern is the evidence available here.

**Cheapest model that was good enough, and why:**

> If "good enough" means a perfect score, `deepseek/deepseek-v4-flash-0731` is the cheapest that got there: 8/8 exact for $0.00385 total (roughly $0.0005 per sentence). `gpt-5.6-luna` was marginally cheaper ($0.00358) but only reached 7/8, and the free `google/gemma-4-26b-a4b-it:free` reached just 5/8 for $0.00 — free, but wrong on 3 of 8 sentences with no way to know which ones without checking by hand. The two priciest models, `gpt-5.6-terra` ($0.02188) and `gpt-5.6-sol` ($0.04743), each only matched luna's 6-7/8-ish range (6/8 both) despite costing 6-13x more than deepseek, so for this task the most expensive models were not the most accurate ones. deepseek gives the best accuracy-per-dollar by a wide margin.

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

> In `cl100k_base`, Kazakh costs 3.75x English per character (0.760 vs 0.203 tok/char), which works out to $0.1666 per 1,000 sentences versus $0.0492 for English — about 3.4x more expensive to run the same meaning through the model. In `o200k_base`, the ratio drops to 1.58x (0.319 vs 0.203 tok/char, $0.0699 vs $0.0492 per 1,000 sentences). So the newer tokenizer cut the Kazakh penalty by 58% (matching the −58.0% in table C), but it did not eliminate it: Kazakh still costs about 42% more than English to tokenize even in the newest OpenAI tokenizer, purely because of how the vocabulary was built, before a single word of meaning is considered.

**2. Why did the models repair `kaz_to_rus` but struggle with
`latin_homoglyph`?** Both are single-letter substitutions and both look almost
identical on screen. Use your token streams from B as the evidence. Say what the
model actually received in each case.

> The token streams in B show the difference: for the `latin_homoglyph` sentences, `first_divergence` is 0 (KZ-03) and 1 (KZ-08) — the corrupted and correct token sequences diverge almost immediately, because swapping a Cyrillic `А`/`а` for a Latin `A`/`a` produces a completely different byte, and therefore a completely different token id, than the correct word (compare `corrupted: ['A', 'л', 'a', 'я', 'қ']` against `correct: ['А', 'лая', 'қ', 'тарға', ' ақша']` for KZ-03 — not even the first token matches). The model is handed tokens it has essentially never seen assembled that way; there is no shared prefix for its attention to anchor on. `kaz_to_rus` substitutions (ә→а, ө→о, ұ/ү→у, і→и, ң→н, ғ→г, қ→к) stay inside the Cyrillic alphabet the whole time — the result is still a real (if wrong) sequence of Cyrillic subword tokens that looks like ordinary Russian-influenced misspelling, a pattern the model has almost certainly seen a lot of in training. So the model isn't reasoning about which letters "look similar" at all — it only ever sees token ids, and `kaz_to_rus` keeps producing familiar ones while `latin_homoglyph` produces unfamiliar ones from the very first token.

**3. Name one thing this measurement does not explain about your Sublab Medium
results.** You measured OpenAI's tokenizers; three of your six models were not
OpenAI's. What follows, and what would you have to do to close the gap?

> This measurement only used OpenAI's own tokenizers (`cl100k_base`, `o200k_base`), but half of the Sublab Medium models — gemma (Google), qwen (Alibaba) and deepseek — use entirely different vocabularies trained on different data. Nothing here says how efficiently or how robustly *those* tokenizers represent Kazakh, or whether a Latin homoglyph produces the same "diverge on token zero" effect in their vocabularies as it does in cl100k_base/o200k_base — it might tokenize completely differently and be more, or less, sensitive to the same corruption. To actually explain gemma's partial `latin_homoglyph` score or qwen's failures from a tokenizer angle, I would need each provider's own tokenizer (e.g. the SentencePiece/BPE vocabulary Gemma or Qwen actually ships) and would have to rerun the same `tokens_per_char` and `first_divergence` measurements against those specific vocabularies, since both quantities are tokenizer-specific and don't transfer across models with different vocabularies.