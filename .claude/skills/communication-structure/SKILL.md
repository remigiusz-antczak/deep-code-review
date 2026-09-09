---
name: communication-structure
description: >-
  Use before sending any human-facing message — a PR body, a GitHub
  issue/PR comment, a status update, or a reply to an owner or colleague.
  Forces BLUF, one ask, zero AI-slop before you draft, not after. Skip for
  chat with the user, which may keep whatever house voice is already set.
license: MIT
metadata:
  author: deep-code-review contributors
  version: "1.0.0"
---

# Communication structure

Governs the *structure* of any message a human reads without you there to
narrate it — a PR body, an issue/PR comment, a status update, a reply. Same
prose-voice boundary as `idea-critic`: persisted artifacts stay normal
English, never compressed chat shorthand. This is about shape and length,
not vocabulary.

## The rule

- **BLUF.** Line 1-2 is the recommendation, answer, or ask. Everything after
  it is support the reader can stop reading at any point without losing the
  decision.
- **One message, one decision.** A yes/no belongs on the last line, explicit,
  A vs. B — never buried mid-paragraph.
- **Under 30 seconds.** ~150 words by default. Longer needs a reason per
  block, or a cut.
- **Scannable.** Bold the one load-bearing sentence. Short paragraphs. A list
  only when every item is parallel and load-bearing — never to pad, and
  never a wall of open questions; keep the 1-2 that actually change the
  decision and push the rest to the doc or PR.
- **Their next action, not your process.** The reader is overloaded and mid
  context-switch. Give them what changes what they do next; drop the
  reasoning trail that got you there.
- **Numbers over adjectives.** "40s to 6s" beats "significantly faster."

## Cut on sight

"You're right" / "great point." Apologizing for the mistake instead of fixing
it. Hedges ("it depends", "I think maybe", "could potentially"). Restating
the question back. Filler adjectives ("comprehensive", "robust",
"seamless"). A summary of the summary. Take a position — if two are
genuinely live, name both and say which you'd pick.

## Sanity check

1. Read line 1 alone. Does it stand as the whole message? If not, promote it.
2. Count the asks. More than one → split, or pick the one that blocks the
   reader.
3. Every paragraph after the first changes what the reader does — or it's
   cut.
4. Scan the draft against "Cut on sight" above.

## Before → After

**Status update.**
Before: "So I looked into why the dashboard was showing no data. I checked a
few things — first thought the build had failed, but it turned out the build
was fine and the issue was downstream. I think the nightly sync job that
populates the dashboard isn't running after a deploy, which would explain
the empty state even though the deploy itself succeeded. Not 100% sure, but
running the sync manually should fix it — let me know if you want me to try
that or if you'd rather take a different approach."
After: "Deploy succeeded; the dashboard is empty because the nightly sync
job never ran after it. **Running it now — confirm it should target
production, not staging.**"

**PR comment, design call.**
Before: "Thanks for looking at this! So for the empty state there are kind
of two ways we could go — a skeleton loader or a 'no data yet' message. Both
have pros and cons. The skeleton is maybe more consistent with the rest of
the app, but the message might be clearer for new users. Curious what you
think, no strong opinion either way, happy to do whatever works best!"
After: "Empty state: skeleton loader (consistent with the rest of the app)
vs. an explicit 'no data yet' message (clearer for first-time users).
**Recommend skeleton — reply A (skeleton) or B (message).**"

**Bug flag to the owner.**
Before: "I think I may have found an issue, not totally sure if it's a real
bug or expected behavior, but wanted to flag it just in case. Looks like the
'Next' button doesn't do anything when clicked, at least on my machine,
though it might just be a caching thing. Let me know if this is known or if
you want me to dig deeper."
After: "The 'Next' button is disabled but styled identically to the active
one — looks clickable, does nothing. **Fixing now; no decision needed.**"
