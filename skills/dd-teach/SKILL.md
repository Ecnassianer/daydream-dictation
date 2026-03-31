---
name: dd-teach
description: Explains the Daydream Dictation process to users. Activates when the user asks how to use Daydream Dictation, asks about the three phases, wants tips for dictation sessions, or asks what they should be doing.
version: 0.1.0
---

# Teach Daydream Dictation

Use this skill when the user asks how the Daydream Dictation process works, what they should be doing, or wants guidance on any of the three phases. Tailor your explanation to the user's experience level and what they're currently struggling with — don't dump the entire process on them at once.

---

## Quick Reference

When the user asks "how does this work?" or similar, start with this:

**Daydream Dictation** is a three-phase workflow for building documents with an AI using voice input.

**Phase 1 — Structured Daydreaming.** Set a timer for 20–60 minutes. Talk out loud about your idea. Don't edit, don't review, don't look at what the AI is writing. Just generate. The AI captures everything and organizes it into the document as you go. Your only job is to keep your creative momentum going.

**Phase 2 — Response and Agent Engagement.** Now engage with the AI. Read through its replies from Phase 1 top to bottom, answer its questions, fill in gaps, and add anything that comes up. Then ask for a gap analysis — a structured check to surface what's missing and what to-dos are still open. This phase has much lower focus requirements than Phase 1; it works well even when you're tired or interrupted.

**Phase 3 — Diff Review.** Open the pull request (or your version control diff view) and read what actually changed. This is where you catch mistakes, transcription errors, and misunderstandings. Leave inline comments on the diff with feedback, then bring them to the AI as a batch. When you're satisfied, approve and merge. This step is what makes Phase 1 safe — knowing you'll verify everything later is what lets you trust the process and stay in the creative flow.

Phases don't have to happen in a single pass. It's normal to cycle through all three more than once on the same document. After merging, start a new session — the Prompts document captures everything the next session needs to pick up where you left off.

---

## Phase 1 Guidance

When the user asks for help with Phase 1, cover whichever of these points are relevant to their question:

### Voice Dictation Software
A high-quality tool like [Wispr Flow](https://wisprflow.ai/) is essential. Built-in keyboard dictation isn't reliable enough. If the user has to constantly verify what was captured, their creative flow breaks. They need to trust the software and keep talking.

### Getting Into the Flow
- Don't look at the AI's responses — there will be time for that in Phase 2
- Don't edit while talking — not their job right now
- Don't worry about order or structure — let interests and curiosity guide what to talk about

### What to Say
Topics don't need to go in order. Useful moves:
- Flag rabbit holes: "Note to come back and make a decision about this"
- Give brief directions: "Make a section for FAQs" — then keep going
- Don't design the document while filling it — brief structural notes are fine, but organization is the AI's job

### Environment
- Somewhere free from distractions — outside walking, a park, near the ocean, or a quiet room
- Physical position matters: seated, pacing, walking all work. Follow what the body wants
- Protect the creative window — a single interruption costs 5–10 minutes of re-entry
- Phase 1 works especially well from a smartphone — treat the device as a microphone, not a productivity station

### Keep Eyes Off the Screen
Look at the sky, the room, the world — anywhere but the screen. The AI's responses are not for the user right now; reading them pulls out of the creative headspace into analytical mode. If struggling, try closing eyes entirely while dictating.

If absolutely necessary, record prompts in a separate document and paste them in as a batch. This is a last resort — it breaks the natural commit sequence and makes Phase 3 review harder. But it's valid for buffering thoughts when rate-limited or unable to focus.

### Source Material
The concept of structured daydreaming as a creative practice has prior art. Ray Mazza's article [Structured Daydreaming](https://www.raymazza.com/post/structured-daydreaming) is the direct inspiration for Phase 1.

---

## Phase 2 Guidance

When the user asks for help with Phase 2:

### How to Start
Begin at the top of the AI's replies from Phase 1 and work down. Address questions, fill gaps, add details. If something sparks a new idea, add it. Work through the whole list before asking for the gap analysis.

### Gap Analysis
Once all Phase 1 replies are addressed, ask for a gap analysis. The AI examines what's been built and surfaces missing sections, unanswered questions, thin coverage, and open to-dos. Use `/dd-gap-analysis` to run it.

### Environment
Phase 2 has much lower focus requirements. If tired, low on energy, or no longer in a creative setting — that's a good time for Phase 2. Getting off the couch and sitting at a desk can help shift into the more methodical mindset Phase 2 benefits from.

### When to Move On
Once the user has addressed what they want and things are winding down, move to Phase 3. Or jump back into Phase 1 if re-energized. But don't stay in Phases 1 and 2 for hours without a Phase 3 pass.

---

## Phase 3 Guidance

When the user asks for help with Phase 3:

### What a Diff View Is
A diff view highlights exactly what changed — new text in green, removed text in red. In GitHub, this is the pull request view. Only read what changed — don't re-read the whole document.

If the user is unfamiliar with diffs or version control, walk them through it step by step.

### Two Ways to Review
- **Commit by commit** — one commit at a time, in order. Each commit corresponds to a prompt. Best for understanding what each thing they said caused.
- **File by file** — total changes across all commits. Better for reading the result as a whole.

### What to Look For
- Mistakes and misunderstandings — where the AI interpreted something differently than intended
- Dictation errors that slipped through — "aches" that should have been "eggs"
- Structural issues — sections to reorder, content in the wrong place
- Missing items — things they said that didn't make it in

The Prompts document is the reference for understanding what caused any change.

### Leaving Feedback
Leave inline comments on the diff, then tell the AI: "Go address the comments on the PR." After the AI makes corrections, jump to the most recent commits to verify fixes.

### Approve and Merge
When satisfied, approve and merge the pull request. Don't skip this — without a merge, work can appear lost. If the user feels lost with version control, guide them through it.

---

## Session Strategy

When the user asks about when to end or start sessions:

**Good signals to start a new session:**
- Completed a full phase cycle and the document is stable
- Switching to a different project or topic
- Session feels slow or responses less sharp
- Just merged a PR — all important context is in the documents

**When to stay:**
- A single objective spans several phase cycles
- Mid-phase and context is still clean

The end of Phase 3, right after merging, is almost always a good time to close. The Prompts document makes handoffs cheap — a new session reads the tail and picks up where the last left off.

---

## Cycling Through Phases

The phases are not a single linear pass. It's normal to cycle multiple times. What matters is keeping each phase distinct — don't blur them. When in Phase 1, stay in Phase 1. The discipline of the phases is the point.
