---
name: daydream-dictation
description: Voice-driven document authoring using the Daydream Dictation three-phase workflow. Use when the user mentions dictation, daydream, Prompts documents, dd-current-dictation-project, voice-to-document workflows, or the three-phase authoring process.
version: 0.1.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Daydream Dictation

## What Is Daydream Dictation?

**Daydream Dictation** is a three-phase workflow for building documents with an AI using voice input.

**Phase 1 — Structured Daydreaming.** Set a timer for 20–60 minutes. Talk out loud about your idea. Don't edit, don't review, don't look at what the AI is writing. Just generate. The AI captures everything and organizes it into the document as you go. Your only job is to keep your creative momentum going.

**Phase 2 — Response and Agent Engagement.** Now engage with the AI. Read through its replies from Phase 1 top to bottom, answer its questions, fill in gaps, and add anything that comes up. Then ask for a gap analysis — a structured check to surface what's missing and what to-dos are still open. This phase has much lower focus requirements than Phase 1; it works well even when you're tired or interrupted.

**Phase 3 — Diff Review.** Open the pull request (or your version control diff view) and read what actually changed. This is where you catch mistakes, transcription errors, and misunderstandings. Leave inline comments on the diff with feedback, then bring them to the AI as a batch. When you're satisfied, approve and merge. This step is what makes Phase 1 safe — knowing you'll verify everything later is what lets you trust the process and stay in the creative flow.

Phases don't have to happen in a single pass. It's normal to cycle through all three more than once on the same document. After merging, start a new session — the Prompts document captures everything the next session needs to pick up where you left off.

---

## Phase 1 — Structured Daydreaming (Detail)

The creative phase. The user stays focused entirely on generating ideas — not paying attention to the AI's responses, not editing, not reviewing. Just talking. Voice dictation captures everything; the AI organizes it into the document as it goes.

The key discipline here is staying in the creative headspace. The AI is still responding throughout — the discipline is the user's job: ignore those responses until Phase 1 is complete.

### Voice Dictation Software

A high-quality, reliable voice dictation tool is a prerequisite. The default Android keyboard dictation or similar built-in options are not good enough. Something like [Wispr Flow](https://wisprflow.ai/) that consistently and accurately captures everything the user says is essential.

If the user has to constantly pause to verify whether the dictation caught their words correctly, their creative flow breaks. They must be able to trust the dictation software and keep going.

The user may maintain a commonly-confused-words file at `.claude/dd-variants.md` listing pairs that their dictation software consistently mis-transcribes. Check for this file and use it to catch likely transcription errors.

### Getting Into the Flow

The overarching goal is that the logistics never disrupt the user's train of thought:
- **Don't look at the AI's responses.** There will be time for that in Phase 2.
- **Don't edit while talking.** Not the user's job right now.
- **Don't worry about order or structure.** Let interests and curiosity guide what to talk about. The AI handles organization.

### What the User Can Say

Topics don't need to go in any particular order. A few useful moves:
- **Flag rabbit holes:** "Note to come back and make a decision about this." The AI marks it; the user deals with it in Phase 2.
- **Give brief directions:** "Make a section for frequently asked questions." "Create a subagent to research X and leave a report." Fire the instruction and keep going.
- **Don't design the document while filling it.** Brief structural notes are fine, but don't stop to think about organization. That's the AI's job.

### Environment and Body Position

Be somewhere free from distractions. Being outside and walking often helps creativity. A quiet room works too. Physical position matters — some people think best seated, others need to pace. Standing and walking can sustain the generative mental state. Follow what the body wants.

A single interruption can cost 5–10 minutes of mental re-entry. Protect the creative window.

### Use a Phone

Phase 1 works especially well from a smartphone — it lets the user move around freely, sit in positions that aren't screen-focused, and use the device primarily as a microphone.

### Keep Eyes Off the Screen

Look at the sky, the room, the world — anywhere but the screen. Let the mind disengage from the recording process and stay in generative thought. If struggling with this, try closing eyes entirely while dictating.

If absolutely necessary, record prompts in a separate document (notes app, Google Doc) and paste them into the agent session in a batch. This is a last resort — it breaks the natural commit sequence and makes Phase 3 review harder.

### Source Material

The concept of structured daydreaming as a creative practice has prior art. Ray Mazza's article [Structured Daydreaming](https://www.raymazza.com/post/structured-daydreaming) is the direct inspiration for Phase 1.

---

## Phase 2 — Response and Agent Engagement (Detail)

The interactive phase. Unlike Phase 1, continuity of thought is not important here. What matters is tracking closely what the AI is doing and moving through each item deliberately — even when topics are completely unrelated. Respond to the AI promptly; this phase is a real back-and-forth.

### Starting Phase 2

Begin at the top of the AI's replies from Phase 1 and work down. Address questions, fill in gaps, and add details as they come up. If something sparks a new idea, add it. Work through the whole list before asking for the gap analysis.

### The Gap Analysis

Once the user has worked through all Phase 1 replies, they ask for a gap analysis. The AI examines what's been built and surfaces areas where the documents can be improved — missing sections, unanswered questions, thin coverage, open to-dos.

The gap analysis also surfaces any to-do items embedded in the documents during Phase 1. Now is a good time to address them, but it's fine to leave them open for a future session.

For the full gap analysis framework, see [Gap Analysis.md](Gap%20Analysis.md).

### Environment and Energy

Phase 2 has much lower environmental requirements than Phase 1. If the user is tired, running low on energy, or no longer in a focused setting — that's a good time to shift into Phase 2. Bounce between topics without worrying about interruptions. Phase 2 is for getting off the couch and sitting at a desk — the more methodical, business-oriented work benefits from a focused (not inspiring) environment.

### When to Move On

Once the user has addressed what they want and the session feels like it's winding down, move to Phase 3. If feeling re-energized, it's fine to jump back into Phase 1. But don't stay locked in Phases 1 and 2 for hours without a Phase 3 pass.

---

## Phase 3 — Diff Review (Detail)

The verification phase. The most procedural of the three. The user reads the actual artifacts the AI created or modified — not the conversation, but the documents themselves, through a diff view. The goal is to verify that every change reflects what was actually intended.

This is the backstop that makes Phase 1 possible. Because Phase 3 exists, the user can let their creative brain run free in Phase 1 without stopping to double-check every AI decision.

### What a Diff View Is

A diff view highlights exactly what changed — new text in green, removed text in red. In GitHub, this is the pull request view. The user only reads what changed, making it fast to catch mistakes.

If the user is unfamiliar with diffs or version control, walk them through it — tell them what to do next.

### Two Ways to Review

- **Commit by commit** — review one commit at a time, in order. Each commit corresponds to a prompt. Best for surgical edits or understanding the AI's reasoning step by step.
- **File by file** — look at total changes across all commits. Better for large new documents.

### What to Look For

- **Mistakes and misunderstandings** — where the AI interpreted something differently than intended
- **Dictation errors that slipped through** — the AI couldn't always resolve transcription ambiguity from context alone ("aches" that should have been "eggs")
- **Structural issues** — sections to reorder, content that needs an intro, things in the wrong place
- **Missing items** — things the user said that didn't make it into the document

The Prompts document is the reference for understanding what caused any change.

### Leaving Feedback

Most code review tools let the user leave inline comments directly on the diff. The user leaves all comments, then tells the AI: "Go address the comments on the PR." The AI reads them and makes corrections. The user can then jump to the most recent commits to verify fixes — a mini Phase 3 within Phase 3.

**How to handle review comments:**
- **Simple changes** (word substitutions, small fixes, clear directives): make the edit, commit, and reply "Done."
- **Complex comments** (questions, design discussions, ambiguous requests): reply with a question or proposed approach before making changes.

### Completing Phase 3 — Approve and Merge

When satisfied, approve and merge the pull request. This makes changes permanent. Don't skip this step — without a merge, it can look like work has been lost.

If the user feels lost with version control at any point, guide them through it.

---

## Cycling Through Phases

The three phases are not a single linear pass. It's common to cycle through all three multiple times on one document. What matters is keeping each phase distinct — don't blur them by reviewing while generating or generating while reviewing. The discipline of the phases is the point.

---

## Session Strategy — When to End and When to Start Fresh

A session has a context window. The Prompts document makes handoffs cheap — a new session reads the tail and picks up where the last left off.

**Good signals to start a new session:**
- Completed a full phase cycle and the document is stable
- Switching to a different project or topic
- Session has been running long and responses feel slower or less sharp
- Just merged a PR — all important context is in the documents

**When to stay in the same session:**
- A single objective spans several phase cycles and will be reviewed/merged together
- Mid-phase and the context is still clean

The end of Phase 3 — right after merging — is almost always a good time to close. Merge promptly, start fresh when ready.
