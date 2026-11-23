# PM004_10 Evaluation: ChatBot - Basics to Advance

23 Nov 2026 · Naveen Nigam

The live run on 23 Nov 2026 confirmed that each level adds what it promises. Only levels 03 to 05 gave Bluewater Bank's real figures. Only levels 04 and 05 took actions, and both asked for approval before blocking a card. Cost per question ranged from USD 0 (Basic) to about USD 0.014 (Agentic). The run found one defect, which was fixed in release 1.0.1.

## 1. What was tested

The same questions went through every level, on the public UAT environment, with real Claude calls. This is the scenario set charter gate G1 asked for.

| Item | Detail |
| --- | --- |
| Date and environment | 23 Nov 2026, UAT (https://chatbot-basics-to-advance-uat.onrender.com), release 1.0.0 |
| Model | Claude Sonnet 5.5 (`claude-sonnet-5-5`) |
| Method | One question per new conversation; answers read from the saved chat history; tokens from the API's `usage` field; time measured in the browser |
| Shared questions (levels 01 to 04) | What is the ATM withdrawal limit? · My payment PAY-1042 hasn't arrived. What should I do? (level 04: What is the status of payment PAY-1042?) · Draft an email to the bank reporting my missing card. |
| Approval check (level 04) | I lost my card, please block it. |
| Agent goals (level 05) | Held payment PAY-1042 needed today · Card lost while travelling · 40,000 in cash today |
| Claude calls used | 18 measured (20 in total, including one first attempt whose results were not captured) |

Each question was run once, so answer length and wording will vary between runs. The figures show the pattern, not exact averages.

## 2. Results by question

Every level behaved as designed except Automation's email draft. Levels without company data said so instead of guessing, and every action waited for the user.

| Question | 01 Basic | 02 Generative AI | 03 RAG | 04 AI Automation |
| --- | --- | --- | --- | --- |
| ATM withdrawal limit | Correct fixed answer: 25,000 per card | Said it cannot know the bank's limit; gave general advice | Correct, cited: 25,000 per card [1] | Correct, cited, from its document search |
| Payment PAY-1042 not arrived | No rule for it; offered the topic menu | Said it cannot see PAY-1042; gave general steps | Said the documents have no full process; cited tracking by reference and the 1-working-day fraud-check release | Payment-status tool: held for a fraud-prevention check, released or returned within 1 working day |
| Email about a missing card | Matched the Cards menu, not the email template (typed text; the menu path works) | Full draft with placeholders; told the user to check official channels | Draft with a warning never to share card number, CVV, PIN or OTP; noted the documents give no reporting channel | **Defect:** the draft was a placeholder that repeated the request (fixed in 1.0.1) |
| Block my card | Not tested | Not tested | Not tested | Asked for approval before blocking; no Claude call |

**Level 05 Agentic AI: the three goals**

| Goal | What the agent did | Verdict |
| --- | --- | --- |
| Held payment PAY-1042, needed today | Looked up the payment status and the documents. Explained the fraud-check hold, the 1-working-day release and the 2 PM same-day cut-off. Took no action, so no ticket was raised when none was needed. | As designed: look before acting |
| Card lost while travelling | Proposed blocking card 4417, explained it cannot be undone and a replacement takes about 5 working days, then asked for approval. Nothing was blocked. | As designed: human approval |
| 40,000 in cash today | Found the 25,000 daily ATM limit per card and the 15,000 shortfall. Said it could not confirm other options (branch withdrawal, temporary limit increase) and the bank must confirm. | As designed: honest about limits |

## 3. Cost and speed

The agent costs about 3 times RAG per question and takes about 11 seconds, so it pays only when the steps are not known in advance. Averages over the three questions per level; cost at USD 2 per million input and USD 10 per million output tokens.

| Level | Claude calls per question | Average cost per question (USD) | Per 1,000 questions (USD) | Average time (s) |
| --- | --- | --- | --- | --- |
| 01 Basic | 0 | 0 | 0 | 0.1 |
| 02 Generative AI | 1 | 0.0083 | 8.33 | 7.2 |
| 03 RAG | 1 | 0.0045 | 4.50 | 4.0 |
| 04 AI Automation | 0 or 1 | 0.0019 | 1.87 | 2.4 |
| 05 Agentic AI | 3 | 0.0140 | 13.99 | 11.3 |

Output tokens were 84% of the cost. Per-question tokens, the price source and the daily worst case are in PM004_07 Token Optimisation, section 5.

## 4. Findings and defects

The run passes charter gate G1 (scenario set run and captured) and supports objective 2 (differences between levels recorded). One defect was fixed and one limitation was accepted.

**What worked**

- **No guessing:** Generative AI never invented the bank's limits or payment status; RAG said when its documents had no answer.
- **Grounding paid twice:** RAG gave the right ATM figure in 96 tokens; Generative AI used 723 tokens to say it could not know.
- **Look before acting:** the agent raised no ticket for the held payment because the lookups already answered it.
- **Human approval:** both levels 04 and 05 asked before blocking a card.

**Defect and limitation log**

| # | Issue | Level | Severity | Action | Status |
| --- | --- | --- | --- | --- | --- |
| D1 | Email draft was a placeholder that repeated the request | 04 AI Automation | Medium: visible on the public demo | Draft now fills the approved missing-card and payment-update templates, with the payment reference filled in when known; new test | Fixed in 1.0.1 |
| D2 | A typed request for a missing-card email opens the Cards menu, not the email template | 01 Basic | Low: the menu path (Write an email) works | Accepted: Basic is menu-first by design | Accepted |

**Improvements to consider**

- Ask level 02 for shorter answers (about 150 words) and lower its `max_tokens`; on these numbers that could halve its cost.
- Run the same question set after each release and add it to this document, with the date and model.

**Lesson for future projects:** run a live scenario set before calling a release done. All 35 offline tests passed, but only real answers exposed a mock tool whose output looked unfinished.
