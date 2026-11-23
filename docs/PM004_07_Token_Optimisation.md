# PM004_07 Token Optimisation: ChatBot - Basics to Advance

23 Nov 2026 · Naveen Nigam

Every Claude call is paid by the token, so this guide records how PM004 keeps token use low, how it measures it, and a checklist to reuse on every future project.

The same techniques apply when the bot is rebuilt or integrated for internal employees (checking leave and other policies, sending out emails): an employee assistant answers far more questions a day, so the savings grow with it.

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

Input tokens (what we send) usually outweigh output tokens (what Claude writes), so most savings come from sending less.

## 2. Techniques used in this project

| # | Technique | Where in the code | What it saves |
|---|---|---|---|
| 1 | **No model call when rules can answer.** Basic menu, approval prompts, declines and "nothing found" replies are written by the app. | `basic()`, approval branch, RAG and Automation no-hit replies | Whole calls |
| 2 | **Retrieve, don't stuff.** Only the best passages (top 3) are sent, and weak matches (less than half the best score) are dropped. | `retrieve()`, `MIN_RELATIVE_SCORE` | Input tokens; also better answers |
| 3 | **Cap the conversation history.** Only the last 8 messages are re-sent each turn, not the whole chat. | `HISTORY_MESSAGES` (env `CHATBOT_HISTORY_MESSAGES`) | Input tokens that would otherwise grow every turn |
| 4 | **Right-size `max_tokens`.** 500 for the agent's internal JSON steps, 1,500 for answers. | `JSON_MAX_TOKENS`, `MAX_TOKENS` | Caps runaway output; you pay only for what is written |
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

To be filled from live runs only (no estimates). Model: `[TBC]`. Date: `[TBC]`.

| Bot | Question | Claude calls | Input tokens | Output tokens |
|---|---|---|---|---|
| 01 Basic | Cards → Block my card | 0 | 0 | 0 |
| 02 Generative AI | I lost my card. What should I do? | [TBC] | [TBC] | [TBC] |
| 03 RAG | I lost my card. What should I do? | [TBC] | [TBC] | [TBC] |
| 04 AI Automation | I lost my card. What should I do? | [TBC] | [TBC] | [TBC] |
| 05 Agentic AI | I lost my card. What should I do? | [TBC] | [TBC] | [TBC] |

Sources: Anthropic documentation on token counting, prompt caching and batch processing (docs.claude.com / platform.claude.com).
