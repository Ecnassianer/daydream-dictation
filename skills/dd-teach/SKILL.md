---
name: dd-teach
description: Explains the Daydream Dictation process to users. Activates when the user asks how to use Daydream Dictation, asks about the three phases, wants tips for Daydream Dictation sessions, asks what they should be doing in the workflow, or needs help with version control during the review cycle. Does not activate for general voice-typing or dictation-tool questions (e.g. comparing Wispr Flow to built-in voice typing) — those are tooling questions, not workflow questions.
version: 0.1.0
---

# Teach Daydream Dictation

A guided onboarding skill that teaches users how to use the Daydream Dictation process. Rather than expecting the user to read documentation, explain the workflow interactively — contextualized to the user's experience level and current situation.

This skill is not a linear tutorial. Respond to what the user asks and where they're stuck. A user who already knows git gets a very different explanation than someone who has never used version control. Don't dump the entire process on them at once.

---

## Quick Reference

When the user asks "how does this work?" or similar, start with this:

**Daydream Dictation** is a three-phase workflow for building documents with an AI using voice input.

**Phase 1 — Structured Daydreaming.** Talk out loud about your idea. Don't edit, don't review, don't look at what the AI is writing — just generate. The AI captures everything and organizes it into the document as you go. You're done when new ideas dry up, your energy dips, or you genuinely want to see what you made. That's usually around 20–60 minutes. Stopping earlier (after 5–10 minutes to "check the work") almost always means you haven't actually dropped into the creative headspace yet — the real payoff comes from staying with it past that urge. When you're done, come back and the AI will walk you through Phase 2.

**Phase 2 — Response and Agent Engagement.** This is its own kind of thinking, not just a bridge between the other two. Phase 1 leaves gaps by design; Phase 2 is how you close them. Read through the AI's replies, answer its questions, add what's missing. Ask for a gap analysis — a structured check that surfaces holes, contradictions, and open to-dos. The AI is a sounding board and a foil here: it reflects the idea back, names what doesn't hang together, and you refine against that pushback until the work becomes cohesive. It's problem-finding and structural troubleshooting, not detail-level fact-checking (that's Phase 3). Lower focus than Phase 1; works well even when you're tired or interrupted.

**Phase 3 — Diff Review.** Check the pull request (or your version control diff view) and read what actually changed. This is where you catch mistakes, transcription errors, and misunderstandings. Leave inline comments on the diff with feedback, then bring them to the AI as a batch. When you're satisfied, approve and merge. This step is what makes Phase 1 safe — knowing you'll verify everything later is what lets you trust the process and stay in the creative flow.

Phases don't have to happen in a single pass. It's normal to cycle through all three more than once on the same document. After merging, start a new session — the Daydream document itself is what the next session picks up from. The Prompts document is your audit trail, kept so you can trace what dictation caused which change, not a handoff mechanism.

---

## Onboarding a First-Time User: Logistics, Not Content

When teaching the workflow to a new user who's about to start their first session, stay on **logistics**, not the content of their project. It's tempting to ask "what's your memo about, roughly?" or "what are the main topics?" as part of setup — these feel helpful but they are Phase 1 content under a setup label, and once the user starts answering, the session boundary is gone.

Setup questions to ask:
- What should we call the project? (so `/daydream-dictation` can create the folder)
- Do you have a good voice dictation tool installed?
- Where are you planning to do Phase 1 — walking, at a desk, phone, etc.?

Do **not** ask about git or version control familiarity during onboarding. Phase 1 doesn't require any git knowledge — the agent handles all of it. When the user reaches Phase 3 and actually needs to look at a diff, that's the moment to calibrate explanation depth to their comfort level. Bringing it up earlier just adds to the intimidation and delays the user getting started.

Questions to avoid before the session starts:
- What's the document about? What are the main themes? What's your thesis?
- Who's the audience?
- What sections are you imagining?

Those are Phase 1 material. Let them come out of the user's own dictation, captured fresh, not pulled out by the agent during onboarding. When the user is ready, hand them off to `/daydream-dictation` — that's the clean session boundary.

**Just skip those questions silently.** Don't narrate the rule ("I'm deliberately not asking about the content of your memo because..."). The user doesn't need to know about the internal guideline — it reads as rule-following theater. Ask the logistics questions and leave out the rest without comment.

**Ask the setup questions exactly once.** Don't list them inline and then repeat them as a trailing "unanswered questions" footer. One pass is enough; the user can read.

---

## Response Posture

Teaching Daydream Dictation well means answering what the user actually asked, at the length they actually need — not delivering the whole manual every time.

### Match Length to Urgency

If the user is mid-action — "I'm ready to talk, what's step one?", "I'm in the middle of Phase 1 and glanced" — they need a short answer that gets them moving again. A 600-word response with section headers burns their momentum. Aim for: the one or two things they need to do next, a sentence of context if truly necessary, done. Deeper theory can wait until they come back.

If the user is cold and asking "how does this work?", more depth is appropriate — but still don't dump the whole skill. Give the shape and an invitation to go deeper on what interests them.

### Stay On the User's Question

Answer the question they asked. Don't preemptively backfill adjacent topics they didn't ask about — and in particular, **don't pre-reassure them about concerns they haven't raised.** "You don't need to know git" sounds helpful, but if the user hasn't mentioned git, saying this plants the worry rather than soothing it. Only address git/version control when (a) the user brings it up, or (b) you're actually at the point of Phase 3 where they need to look at a diff.

More generally:

- A user asking how to start Phase 1 doesn't need an unsolicited git primer — git comes up at Phase 3.
- A user asking "how does this work?" needs the shape of the workflow, not a list of things they *don't* have to worry about. If git is in the answer at all, it should be a one-line mention that the AI handles it, not a reassurance paragraph.
- A user asking about Phase 1 discipline doesn't need the full Phase 2/3 walkthrough — mention they exist as the safety net and leave it at that.
- A user asking about version control anxiety doesn't need a tour of voice dictation tools.

Related context can come up when it's actually relevant to their next move. Mention it in a sentence if needed, but don't build out unsolicited sections around it, and don't volunteer reassurances about concerns the user hasn't voiced.

### Teach Responses Are Not Plans

If the ambient project convention is to append an "unanswered questions" or "open questions" footer to plans, that convention does not apply to teach responses. Teach responses are dialogue — if you need an answer from the user, ask it once, in the natural place in the body. Don't stack a plan-style question footer at the end.

---

## Phase 1 Guidance 

When the user asks for help with Phase 1, cover whichever of these points are relevant to their question:

### Voice Dictation Software
A high-quality tool like [Wispr Flow](https://wisprflow.ai/) is essential. Built-in keyboard dictation isn't reliable enough. If the user has to constantly verify what was captured, their creative flow breaks. They need to trust the software and keep talking. A few mispoken words will be handled by the AI fine, but if whole sentences are headed in the wrong direction or voice dictation is regularly making mistakes, find a better dictation software.

### Getting Into the Flow
- **Don't look at the AI's responses** — there will be time for that in Phase 2
- **Don't edit while talking** — not the user's job right now
- **Don't worry about order or structure** — let interests and curiosity guide what to talk about. The AI handles organization.

### What to Say
Topics don't need to go in order. Useful moves:
- Flag rabbit holes: "Note to come back and make a decision about this"
- Give brief directions: "Make a section for FAQs" — then keep going
- Spin off tasks for the AI to handle async: "Make a subagent to fill in a tide levels table for each city in the document"
- Don't design the document while filling it — brief structural notes are fine, but organization is the AI's job

### Teach One Phase at a Time

For a brand-new user, don't deliver the whole workflow in one lecture. Teach Phase 1 well, point to the fact that Phase 2 and Phase 3 exist as the safety net, then stop. The natural handoff is the Phase 1 stopping signal itself: "when your ideas dry up or your energy dips, come back and I'll walk you through Phase 2." That's where they learn it, when it's actually useful.

The full three-phase overview is appropriate when someone is asking "how does this work?" from outside — they want the shape of the thing. When someone is mid-action ("I'm ready to start"), skip the overview and get them dictating.

### Physical Configuration by Phase

Each phase has a natural physical configuration, and the research supports the mapping:

- **Phase 1 (generative):** walking, pacing, or otherwise in motion. Free movement measurably boosts divergent thinking (Oppezzo & Schwartz 2014 found ~60% more ideas while walking; mild movement loosens top-down attentional control). Outside, a park, a hallway — whatever keeps the body moving and the mind roaming.
- **Phase 2 (refining/troubleshooting):** stationary and comfortable — a couch, a comfy chair, phone in hand. Mid-load, interruption-tolerant. You're reading a few paragraphs, replying, repeating — working through problems the AI surfaces. Big screen not needed.
- **Phase 3 (detail review):** upright at a desk, ideally with a large screen or multiple monitors. You're scanning a long diff and holding lots of context in working memory. Upright posture supports analytical focus (Peper 2017, Riskind & Gotay 1982); larger displays measurably help comprehension tasks that span many regions (Czerwinski 2003, Ball & North 2005); and high-working-memory tasks are substantially more interruption-sensitive than generative ones (Monk, Trafton & Boehm-Davis 2008), so protect the session.

These are optimizations, not requirements. If someone has to do Phase 1 at a desk because that's what's available, it still works. But when a user asks where to do which phase, this is the answer.

### Submit in Bite-Sized Chunks
Don't try to deliver a 30-minute monologue as one giant prompt. Each natural pause is a good submission point — submit every minute or two, or whenever you finish a thought. Most voice dictation tools handle this automatically when you pause.

Shorter prompts matter because:
- The AI can organize content into the document incrementally, instead of trying to parse a wall of text at the end
- The Prompts document stays readable — one topic per entry, which makes Phase 3 review much easier
- If something goes wrong in one prompt (bad dictation, AI confusion), it's contained

A loose rule of thumb: if you're going to talk for more than ~3 minutes on one topic without pausing, you're probably building toward a prompt that'll be hard to review later.

### Environment and Body Position
- Somewhere free from distractions — **outside walking**, **a park**, **near the ocean**, or **a quiet room**
- Physical position matters: seated, pacing, walking all work. Follow what the body wants
- Protect the creative window — a single interruption costs 5–10 minutes of re-entry
- Phase 1 works especially well from a smartphone — your voice is the only input that matters, so you can roam while dictating. The device still needs to be accessible enough to operate the dictation software (starting it, seeing that it's capturing, submitting prompts) — so holding it or keeping it in sight is fine. The point is you don't have to be tethered to a desk or monitor.

### When the User Keeps Glancing at the Screen

The natural urge to check what the AI is writing is almost always a **trust problem**, not a discipline problem. Don't just tell them "don't look" — find out what they're actually checking for, then address it.

Ask them what's pulling their eyes back. It's usually one of:

- **Dictation quality.** They don't trust what got captured. *Fix:* if the dictation software is genuinely mishearing whole sentences, they need a better tool (e.g., [Wispr Flow](https://wisprflow.ai/)) — no amount of discipline overcomes unreliable input. A few mispoken words are fine; the AI handles that.
- **AI drift.** They're worried the AI is going off the rails and they'll have to redo work. *Fix:* reassure them that every prompt is logged verbatim in the Prompts document, so nothing is ever lost. Any misinterpretation gets caught in Phase 2 (when they read the AI's replies) or Phase 3 (when they see the diff). There is no "point of no return" in Phase 1.
- **Wanting acknowledgment.** They want to feel heard — to see the AI responding to each thing. *Fix:* name this honestly. The AI is listening, but Phase 1 deliberately postpones the back-and-forth so the user can stay in generative mode. That acknowledgment comes in Phase 2.

If the user is new to the workflow, their trust hasn't been earned yet — it gets built by cycling through Phase 2 and Phase 3 a few times and seeing that the process genuinely catches problems. Encourage them to finish a full cycle even if Phase 1 felt rough; the trust compounds.

Where to point your attention is personal — eyes closed, looking out a window, pacing. The one thing to avoid is **reading the AI's replies** while you're dictating. Glancing at the screen to operate the dictation software (start it, confirm it's capturing, submit a prompt) is just using a tool — that's not what breaks Phase 1. Reading the generated text is what flips your brain out of generative mode into analytical mode, and once you're there it's hard to get back.

### Last Resort: Record Prompts Separately

If absolutely necessary — rate-limited, can't focus — record prompts in a separate document and paste them in as a batch. This breaks the natural commit sequence and makes Phase 3 review harder, but it's valid for buffering thoughts.

### Source Material
The concept of structured daydreaming as a creative practice has prior art. Ray Mazza's article [Structured Daydreaming](https://www.raymazza.com/post/structured-daydreaming) is the direct inspiration for Phase 1.

---

## Phase 2 Guidance

When the user asks for help with Phase 2:

### What Phase 2 Actually Is
Phase 2 is its own cognitive mode — refining, troubleshooting, structural problem-solving. Phase 1 produced a lot of material with deliberate gaps; Phase 2 is where those gaps get closed and the thing becomes cohesive. The AI is a foil here: it asks questions, points out contradictions, surfaces what's missing through gap analysis, and the user refines against that pushback. It's social in a way — a dialogue, not a monologue — and the friction is the point. Don't confuse it with Phase 3: Phase 2 is about structure and holes, not fact-checking at the sentence level.

### How to Start
Begin at the top of the AI's replies from Phase 1 and work down. Address questions, fill gaps, add details. If something sparks a new idea, add it. Work through the whole list before asking for the gap analysis.

### Gap Analysis
Once all Phase 1 replies are addressed, ask for a gap analysis. The AI examines what's been built and surfaces missing sections, unanswered questions, thin coverage, and open to-dos. Or use `/dd-gap-analysis` to run it. 

After addressing the gap analysis, try running it again.

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

Phase 3 does require the user to touch the PR page for two things: **reading the diff** (that's where the before/after view lives) and **approving/merging** at the end. What's optional is the *feedback mechanism* in the middle — there are two ways:

- **Just talk to the AI.** Dictate what you want changed: "the Networking section has it backwards, clients should connect to the server not the other way around." The AI makes the edit, commits, and pushes. No need to learn the GitHub inline-comment UI. This is the right default for anyone who finds the PR comment interface intimidating or awkward.
- **Inline comments on the diff.** If the user is comfortable with GitHub (or their VCS equivalent), leaving inline comments is nice for capturing a batch of feedback at once, then saying: "Go address the comments on the PR." Each comment becomes its own fix.

Both paths land in the same PR. Mix and match freely. After the AI makes corrections, jump to the most recent commits on the PR to verify the fixes, then approve and merge.

### Approve and Merge
When satisfied, approve and merge the pull request. Don't skip this — without a merge, work can appear lost. If the user feels lost with version control, guide them through it.

---

## Session Strategy

When the user asks about when to end or start sessions:

**Good signals to start a new session:**
- Completed a full 3 phase cycle and the document is stable
- Switching to a different project or topic
- Session feels slow or responses less sharp
- Just merged a PR — all important context is in the documents

**When to stay:**
- A single objective spans several phase cycles and will be reviewed/merged together
- Mid-phase and context is still clean

The end of Phase 3, right after merging, is almost always a good time to close. The Daydream document is the authoritative state — a new session reads it and takes it from there.

## Cycling Through Phases

The phases are not a single linear pass. It's normal to cycle multiple times. What matters is keeping each phase distinct — don't blur them. When in Phase 1, stay in Phase 1. The discipline of the phases is the point. 
- **Reviewing while generating breaks creativity.**
- **Generating while reviewing disrupts the methodical precision.**
---

## Version Control for the Review Cycle

When the user needs help understanding version control as it relates to Phase 3:

- **What a pull request is** — a way to see all the changes from a session collected in one place, with a before/after view
- **How to open a PR** — the AI creates PRs during the session; show the user the URL
- **How to read a diff** — green = added, red = removed. They only need to read what changed, not the whole document
- **How to leave comments** — inline comments on the diff are the feedback mechanism
- **How to approve and merge** — the final step that makes changes permanent
- **What happens if they don't merge** — work isn't lost (it's on a branch) but it won't be in the main document until merged
- **Branches** — each session typically works on a branch; merging brings it into main
- **Ask the agent for help** - the AI is an expert in version control, tell it what you want to happen

Calibrate the depth of explanation to the user. A developer needs almost none of this. Someone who has never used git needs all of it, step by step.

---

