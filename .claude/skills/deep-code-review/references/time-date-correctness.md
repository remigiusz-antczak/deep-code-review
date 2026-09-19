# Time, dates & time zones

Read this when reviewing anything that **stores, computes, schedules, or renders**
timestamps, durations, recurring events, or calendar math — especially across time
zones or a DST transition. Expands domain **A** of `SKILL.md`; cross-ref domain **W**
(`domain-checklists.md`, cron/jobs) and domain **E** (`billing-correctness.md`, usage
windows). The one-line rule in `domain-checklists.md` domain A points here for depth.

---

## The distinction everything hangs on: an *instant* vs a *wall-clock* time

- An **instant** (exact / absolute time) is the same everywhere — a log line, a
  `created_at`, an event that already happened. Store it in **UTC**, render it in the
  viewer's zone. "Store in UTC" is correct **here**.
- A **wall-clock time** (local / clock time) is what a human reads off a clock —
  "9:00 am", "the 1st of the month" — and is meaningful only against a time zone. TC39
  Temporal draws the line: wall-clock time "depends on the time zone of the clock" while
  exact time "is the same everywhere"; a zoned datetime "encapsulates ... an exact time
  ... its wall-clock equivalent ... and the time zone that links the two." Local rules
  are set by governments and can change abruptly. (A wall-clock value carried with **no**
  zone at all — a "floating" time — is a third, weaker thing: "the same clock reading
  everywhere," which is *not* what a per-zone recurrence wants.)
- **The finding.** A **wall-clock-anchored recurring** event — a daily 9am reminder, a
  recurring meeting, a monthly invoice date — that bakes in a **single UTC instant at
  creation** drifts by the DST offset after a transition (9am silently becomes 8am or
  10am). The blanket rule "store *everything* in UTC" is **wrong** for this case. Store
  the **local wall-clock time + the tz-id** and **re-resolve the UTC offset per
  occurrence**, not once. Match the representation to the feature: a past/point instant
  → UTC; a future wall-clock commitment or recurrence → local time + tz-id, resolved to
  an instant late (at/near each occurrence).

## Ambiguous & missing local times at a DST transition

At a transition a local time is either **ambiguous** or **missing**, and code that
assumes every local time maps to exactly one instant is wrong at both. Require an
**explicit, documented disambiguation rule**; Python's PEP 495 names the cases: "A
local time that falls in the fold is called *ambiguous*" (fall-back: the hour repeats,
so the local time occurs **twice**) and "A local time that falls in the gap is called
*missing*" (spring-forward: the hour is skipped, so the local time occurs **never**),
with the invariant that "The `fromutc()` method should never produce a time in the
gap." Decide the rule explicitly: for an **ambiguous** time pick the earlier or later
occurrence deliberately (PEP 495's `fold`); for a **missing** time, map it forward to
the post-transition instant or reject it — never leave the choice to a library default.
A scheduler that fires a "2:30 am" job on the spring-forward night, or runs a
fold-hour job twice or zero times, is the finding (same root as the cron DST
double/zero-run in `domain-checklists.md` domain W).

## The tz database is a dependency that goes stale

Time-zone rules are **data** (the IANA `tz` database, or the platform's ICU), not code,
and change with little notice — so a **future** timestamp converted *before* a rule
change is silently wrong *after* it. IANA's own theory file: "The `tz` database
predicts future timestamps, and current predictions will be incorrect after future
governments change the rules ... if today someone schedules a meeting for 13:00 next
October 1, Dublin time, and tomorrow Ireland changes its daylight saving rules,
software can mess up after the rule change if it blithely relies on conversions made
before the change." Check: the tzdata / ICU version is **pinned and has a real update
path** (a refreshed base image, bundled ICU, or vendored tzdata — not a frozen copy),
and future wall-clock commitments are **re-resolved after a tzdata update**, not frozen
to an instant at creation.

## Durations: monotonic, and not 86,400-per-day

Measure **elapsed time** with a **monotonic** clock, never wall-clock subtraction — a
wall clock can jump backward or forward (an NTP step, a DST change, a leap second) and
yield a negative or wildly wrong duration. Do not assume a **calendar day** is exactly
86,400 seconds — a DST-transition day is 23 or 25 hours (and a leap second adds one), so
"one day later" is not reliably `+86,400 s`, nor an hour always 3,600. A leap second also
breaks fixed-second arithmetic, and one common
mitigation is a **leap smear** — Google "'smeared' the extra second across the hours
before and after each leap" — but a review confirms the approach is **chosen and
consistent** across the fleet (a smeared client against a stepped server disagree by up
to a second), not that `86400` was hard-coded.

**🚩 red flags**: a recurring wall-clock event stored as one fixed UTC instant; a
future local time whose offset is frozen at creation; a local↔instant conversion with
no fold/gap (ambiguous/missing) handling; `now()`/`datetime.now()` naive (no tz);
wall-clock subtraction for a duration or timeout; a hard-coded `86400` / `3600*24`;
tzdata/ICU with no version pin or no update path; a blanket "store everything in UTC"
applied to a wall-clock-anchored recurrence.
