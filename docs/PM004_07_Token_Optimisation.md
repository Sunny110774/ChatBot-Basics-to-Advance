# PM004_07 Token Optimisation: ChatBot - Basics to Advance

23 Nov 2026 · Naveen Nigam

Every Claude call is paid by the token, so this guide records how PM004 keeps token use low, how it measures it, and a checklist to reuse on every future project.

The same techniques apply when the bot is rebuilt or integrated for internal employees (checking leave and other policies, sending out emails): an employee assistant answers far more questions a day, so the savings grow with it.

Cost is one of the guardrails of a live AI system: the daily call caps, history cap and output token caps below sit alongside the safety guardrails listed in the README and charter (section 6.7).

**At a glance**
- **Rule 1:** don't call the model when rules or data can answer.
- **Rule 2:** send the model only what it needs (relevant passages, recent turns).
- **Rule 3:** combine small jobs into one call (answer + follow-ups + verify).
- **Rule 4:** measure every call; optimise from numbers, not guesses.

## 1. Where the tokens go

Each answer shows its cost in "What this level did" (**Cost:** calls, input and output tokens, split by step). The numbers come from the `usage` field Claude returns with every reply.

| Bot | Claude calls per question | When it makes no call at all |
|---|---|---|
| 01 Basic | 0 | Always: fixed rules only |
| 02 Generative AI | 1 | Never |
| 03 RAG | 1 | Nothing relevant found in the documents: it says so instead of guessing |
| 04 AI Automation | 1 | Asking for approval; you decline an action; nothing found in the fallback search |
| 05 Agentic AI | 3 (plan, decide, answer + verify) | You decline an action |

Measured on 23 Nov 2026 (section 5), **output tokens drive the cost**: each output token costs five times an input token on Claude Sonnet 5.5, so output was 84% of the measured cost. So the biggest savings come from shorter answers and fewer calls; sending less still matters as history grows.

## 2. Techniques used in this project

| # | Technique | Where in the code | What it saves |
|---|---|---|---|
| 1 | **No model call when rules can answer.** Basic menu, approval prompts, declines and "nothing found" replies are written by the app. | `basic()`, approval branch, RAG and Automation no-hit replies | Whole calls |
| 2 | **Retrieve, don't stuff.** Only the best passages (top 3) are sent, and weak matches (less than half the best score) are dropped. | `retrieve()`, `MIN_RELATIVE_SCORE` | Input tokens; also better answers |
| 3 | **Cap the conversation history.** Only the last 8 messages are re-sent each turn, not the whole chat. | `HISTORY_MESSAGES` (env `CHATBOT_HISTORY_MESSAGES`) | Input tokens that would otherwise grow every turn |
| 4 | **Right-size `max_tokens`.** 800 for the agent's internal JSON steps, 1,500 for answers. | `JSON_MAX_TOKENS`, `MAX_TOKENS` | Caps runaway output; you pay only for what is written |
| 5 | **Combine jobs in one call.** Follow-up suggestions ride on the answer (`FOLLOW-UPS:` line); the agent's goal check rides on its reply (`VERIFY:` line). | `split_follow_ups()`, `finish_verify()` | One call per answer, and a fourth call in level 05 |
| 6 | **Fixed follow-ups where the options are known.** Automation's next steps come from a list, not from Claude. | `NEXT_TASKS`, `automation_follow_ups()` | Output tokens |
| 7 | **Short, structured internal outputs.** The agent's plan and decision are compact JSON, not prose. | Agent plan and decide prompts | Output tokens |
| 8 | **Ask for short replies.** The agent's customer reply is capped at about 120 words; internals go to the panel, not the reply. | Agent answer prompt | Output tokens |
| 9 | **Free connection test.** The Settings **Test** button uses the token-counting endpoint, which Anthropic documents as free to use (rate-limited); very old SDKs fall back to a 1-token reply. | `test_connection()` | A paid call on every test |
| 10 | **Measure every call.** Calls and tokens per step are stored with each answer. | `llm()`, `USAGE`, `meta["usage"]` | Makes the rest measurable |

## 3. Worth adding at scale (not used here yet)

| Technique | What it does | When it pays off |
|---|---|---|
| **Prompt caching** | Re-uses a long, unchanging prompt prefix (system prompt, documents, tool list). Cache writes cost more than normal input (1.25x for a 5-minute cache, 2x for 1 hour); cache reads cost a small fraction of normal input. | Long, stable prefixes re-sent many times. PM004's prompts are short and probably below the minimum cacheable length, so it is not used here. Check the minimum for your model in Anthropic's docs. |
| **Message Batches API** | Sends many requests together, processed asynchronously at 50% of standard prices. | Work nobody is waiting for: evaluations, nightly summaries, bulk classification. |
| **Model routing** | Uses a smaller, cheaper model for simple internal steps (the agent's plan and decision) and the main model for the customer reply. | Multi-call flows such as level 05. Test that quality holds first. |
| **Summarise old history** | Replaces older turns with a short summary instead of dropping them. | Long conversations where early context still matters. |

## 4. Checklist for every future project

1. **Can rules or data answer this without a model?** If yes, don't call Claude.
2. **Is every token in the prompt needed?** Send retrieved passages, not whole documents; drop weak matches.
3. **Is history capped?** Set a limit and make it configurable.
4. **Is `max_tokens` set per step?** Small for internal steps, larger for answers.
5. **Can two calls become one?** Ask for extra parts (follow-ups, checks) as tagged lines in the same reply.
6. **Are internal outputs structured and short?** JSON for machine steps; prose only for people.
7. **Is usage measured and shown?** Log input and output tokens per step from the API's `usage` field.
8. **At scale:** consider prompt caching for long stable prefixes, batches for work nobody waits for, and smaller models for simple steps.
9. **Record the measured cost per question** in the evaluation document, with the date and model.

## 5. Measured results

Measured live on UAT on 23 Nov 2026 with Claude Sonnet 5.5, one question per new conversation, token counts from the API's `usage` field. Cost uses list prices of USD 2 per million input tokens and USD 10 per million output tokens. Each question was run once; answer length varies from run to run.

| Bot | Question | Claude calls | Input tokens | Output tokens | Cost (USD) | Time (s) |
|---|---|---|---|---|---|---|
| 01 Basic | Any of the three questions | 0 | 0 | 0 | 0 | 0.1 |
| 02 Generative AI | What is the ATM withdrawal limit? | 1 | 223 | 723 | 0.0077 | 6.7 |
| 02 Generative AI | My payment PAY-1042 hasn't arrived. What should I do? | 1 | 232 | 760 | 0.0081 | 7.2 |
| 02 Generative AI | Draft an email to the bank reporting my missing card. | 1 | 226 | 880 | 0.0093 | 7.7 |
| 03 RAG | What is the ATM withdrawal limit? | 1 | 310 | 96 | 0.0016 | 2.1 |
| 03 RAG | My payment PAY-1042 hasn't arrived. What should I do? | 1 | 336 | 383 | 0.0045 | 4.0 |
| 03 RAG | Draft an email to the bank reporting my missing card. | 1 | 312 | 679 | 0.0074 | 6.0 |
| 04 AI Automation | What is the ATM withdrawal limit? | 1 | 211 | 28 | 0.0007 | 1.9 |
| 04 AI Automation | What is the status of payment PAY-1042? | 1 | 231 | 90 | 0.0014 | 2.0 |
| 04 AI Automation | Draft an email to the bank reporting my missing card. | 1 | 228 | 309 | 0.0035 | 3.2 |
| 04 AI Automation | I lost my card, please block it. (asks for approval) | 0 | 0 | 0 | 0 | 0.2 |
| 05 Agentic AI | My payment PAY-1042 hasn't arrived and I need it sorted today. | 3 | 1,957 | 877 | 0.0127 | 9.3 |
| 05 Agentic AI | I lost my card while travelling. Sort it out. | 3 | 1,308 | 1,026 | 0.0129 | 11.3 |
| 05 Agentic AI | I need 40,000 in cash today. Work out how I can get it. | 3 | 1,362 | 1,369 | 0.0164 | 13.4 |

**Average per question and per 1,000 questions**

| Bot | Average cost per question (USD) | Per 1,000 questions (USD) | Average time (s) |
|---|---|---|---|
| 01 Basic | 0 | 0 | 0.1 |
| 02 Generative AI | 0.0083 | 8.33 | 7.2 |
| 03 RAG | 0.0045 | 4.50 | 4.0 |
| 04 AI Automation | 0.0019 | 1.87 | 2.4 |
| 05 Agentic AI | 0.0140 | 13.99 | 11.3 |

**What the numbers show**
- **Output is most of the bill.** Across all 12 answers that called Claude, output tokens were 84% of the cost (40% to 95% per answer; only the shortest answers were cheaper on output than input).
- **Grounding made answers cheaper as well as correct.** For the ATM question, RAG wrote 96 tokens with the right figure; Generative AI wrote 723 tokens explaining it could not know. Generative AI cost about twice as much as RAG per question.
- **The agent costs about 1.7 times Generative AI, 3 times RAG and 7 times Automation per question,** and takes 9 to 13 seconds. It is worth it only when the steps are not known in advance.
- **Rules first saves whole calls.** Basic and the approval prompt cost nothing.
- **Worst-case daily spend is small because of the caps.** Prod allows 300 Claude calls a day: about USD 2.80 if every call were a long Generative answer, about USD 1.64 if every question went to the agent. UAT (100 calls) stays under USD 1 a day.

**Next saving to try:** ask level 02 for shorter answers (for example, at most 150 words) and lower its `max_tokens`. On these numbers that could cut its cost by about half. Not done yet; test that answer quality holds first.

Price source: Anthropic's list price for Claude Sonnet 5.5, as reported in November 2026 (USD 2 input, USD 10 output per million tokens). Check the current price in Anthropic's pricing documentation before reusing these figures.

Sources: Anthropic documentation on token counting, prompt caching and batch processing (docs.claude.com / platform.claude.com).
