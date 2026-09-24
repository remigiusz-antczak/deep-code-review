# Parity capture contract (template)

Copy this into the target repo and fill in the placeholders. It defines how both renders (design and app)
are exported for `scripts/parity_differ.py` so that the comparison runs on populated, signed-in, same-state
pages. Nothing here runs in CI: the snippet is a template for the project's own harness.

## What each capture must produce

For every page in the correspondence table, at every viewport in the list below, on **both** sides:

1. **Data-settled, not just hydrated (#1165).** A route with a serial/waterfall fetch chain (one
   request kicked off only after the previous resolves) can still be capturing while its data loads —
   DOM-hydrated and data-settled are two different signals that can complete far apart in time, and a
   capture taken between them scores as a large mismatch that is pure timing, never real divergence.
   Wait for an **app-declared settle signal** — the app sets `document.documentElement.dataset.parityReady
   = "1"` once its loading state clears everywhere (not only for the first component) — or, when the app
   exposes none, network-idle for a fixed window (`N` ms with no new request) after the *last* request in
   the chain, bounded to a documented max wait so a genuinely-broken fetch cannot hang the capture forever.
   Record the outcome on the capture itself: set `data-parity-ready="1"` or `"0"` and
   `data-parity-settle-ms="<elapsed>"` on the document (the Playwright snippet below does this).
   `parity_differ.py` reads that marker: `"0"` is `COULD_NOT_CHECK` for the whole comparison, never scored
   as a mismatch; with `--require-settled` a capture carrying no marker at all is the same
   `COULD_NOT_CHECK` (an older capture cannot certify it settled). Treat a first low score as provisional —
   re-check with a longer settle window before reporting it as a real difference.
2. `<out>/<side>/<page>@<width>.html` is a DOM snapshot after the page settles. Every section root carries
   `data-section="<id>"` (the same ids on both sides), and populated units carry `data-item`.
3. **Computed styles.** Every visible text-bearing element that should be style-checked carries a
   `data-cs` JSON object with a non-empty value for each property the differ compares (`font-family`,
   `font-size`, `font-weight`, `line-height`, `letter-spacing`, `color`, `background-color`, `padding`,
   `border-radius`, `box-shadow`). Values come from `getComputedStyle`, exported in the same browser for
   both sides.
4. **Visibility markers.** Every element whose class hides it through a stylesheet (`hidden`, `sr-only`,
   `invisible`, `d-none`, `visually-hidden`) carries `data-visible="true"` or `"false"`, read from
   `checkVisibility()`.
5. Optional section screenshots: `<out>/<side>-shots/<page>@<width>/<section id>.png`. Pass that folder
   to `--design-shots` / `--app-shots` together with `--report`.
6. **Band markers (only with `BANDS=1`, for `parity_differ.py --bands headings`).** Use this when the design
   and the app nest a section differently, so `data-section` ancestors would crop different regions. Every
   element under `<body>` carries `data-y`, its integer top y in page coordinates. Section titles that are
   not h1/h2 carry `data-anchor` on both sides. The screenshots become heading y-band clips named by band
   id. The top y only places an element in a band; it is never a parity signal (SECTION BANDS in
   `parity_differ.py`).

## Same state on both sides (the precondition)

| Input | Where it comes from | Rule |
|---|---|---|
| `DEV_IDENTITY` | env, e.g. `DEV_IDENTITY=persona-analyst` | A fictional, seeded persona. It is never a real account. |
| `AUTH_COOKIE` | env: the name=value of a dev session cookie for that persona | Keep it in env or a gitignored file. Never commit it. |
| `SEED_CMD` | env, e.g. `SEED_CMD="make seed-dev"` | Idempotent, dev-only, and it writes through the app's own create paths. Run it before every app capture. |
| `VIEWPORTS` | fixed list, e.g. `1440x900,1024x768,390x844` | Use the same list for both sides and every run. |

The signed-out default surface is a separate capture (no identity, no cookie) and gets its own parity
check. This matched-state capture does not replace it.

## Playwright snippet (template only)

```js
// capture.mjs: node capture.mjs <side> <url> <page>
import { chromium } from "playwright";
import { execSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";

const [side, url, page] = process.argv.slice(2);
const BANDS = Boolean(process.env.BANDS);
const PROPS = ["font-family", "font-size", "font-weight", "line-height", "letter-spacing", "color",
  "background-color", "padding", "border-radius", "box-shadow"];
if (side === "app" && process.env.SEED_CMD) execSync(process.env.SEED_CMD, { stdio: "inherit" });

const browser = await chromium.launch();
for (const vp of (process.env.VIEWPORTS || "1440x900").split(",")) {
  const [width, height] = vp.split("x").map(Number);
  const ctx = await browser.newContext({ viewport: { width, height } });
  if (process.env.AUTH_COOKIE) {
    const [name, ...rest] = process.env.AUTH_COOKIE.split("=");
    await ctx.addCookies([{ name, value: rest.join("="), url }]);
  }
  const tab = await ctx.newPage();
  await tab.goto(url, { waitUntil: "domcontentloaded" });
  // Data-settled, not just hydrated (#1165): prefer the app's own signal -- it alone knows
  // when a serial/waterfall fetch chain, not only the first batch, has cleared everywhere.
  // Bounded max wait either way, so a genuinely-broken fetch cannot hang the capture forever.
  const READY_TIMEOUT_MS = Number(process.env.PARITY_READY_TIMEOUT_MS || 15000);
  const settleStart = Date.now();
  let ready;
  try {
    await tab.waitForFunction(() => document.documentElement.dataset.parityReady === "1",
      null, { timeout: READY_TIMEOUT_MS });
    ready = true;
  } catch {
    // No app-declared marker (or it never fired): fall back to network-idle for the tail of
    // the chain, re-checked here (not only at goto), since a late fetch starts after goto settles.
    ready = await tab.waitForLoadState("networkidle", { timeout: READY_TIMEOUT_MS }).then(() => true, () => false);
  }
  const settleMs = Date.now() - settleStart;
  await tab.evaluate(([r, ms]) => {
    document.documentElement.setAttribute("data-parity-ready", r ? "1" : "0");
    document.documentElement.setAttribute("data-parity-settle-ms", String(ms));
  }, [ready, settleMs]);
  await tab.evaluate(([props, bands]) => {
    for (const el of document.querySelectorAll(bands ? "body *" : "[data-section] *")) {
      if (bands) el.setAttribute("data-y", String(Math.round(el.getBoundingClientRect().top + scrollY)));
      if (/\b(hidden|sr-only|invisible|d-none|visually-hidden)\b/.test(el.getAttribute("class") || "")) {
        el.setAttribute("data-visible", String(el.checkVisibility()));
      }
      const own = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
      if (own && el.checkVisibility()) {
        const cs = getComputedStyle(el);
        el.setAttribute("data-cs", JSON.stringify(Object.fromEntries(props.map((p) => [p, cs.getPropertyValue(p)]))));
      }
    }
  }, [PROPS, BANDS]);
  mkdirSync(`out/${side}`, { recursive: true });
  writeFileSync(`out/${side}/${page}@${width}.html`, await tab.content());
  const shots = `out/${side}-shots/${page}@${width}`;
  mkdirSync(shots, { recursive: true });
  if (BANDS) {
    // Band starts as the differ computes them: data-anchor elements win, else h1/h2; same top y folds.
    const bands = await tab.evaluate(() => {
      const top = (el) => Math.round(el.getBoundingClientRect().top + scrollY);
      const text = (el) => el.textContent.replace(/\s+/g, " ").trim().toLowerCase();
      let cands = [...document.querySelectorAll("[data-anchor]")].filter((el) => el.checkVisibility() && text(el));
      const level = (el) => el.getAttribute("role") === "heading" ? Number(el.getAttribute("aria-level") || 2)
        : Number(el.tagName[1]);
      if (!cands.length) cands = [...document.querySelectorAll("h1, h2, [role=heading]")].filter((el) =>
        el.checkVisibility() && text(el) && level(el) <= 2);
      const seen = new Set(), count = {}, out = [{ id: "(page header)", y: 0 }];
      for (const el of cands.sort((a, b) => top(a) - top(b))) {
        if (seen.has(top(el))) continue;
        seen.add(top(el));
        count[text(el)] = (count[text(el)] || 0) + 1;
        out.push({ id: text(el) + (count[text(el)] > 1 ? ` #${count[text(el)]}` : ""), y: top(el) });
      }
      return out.map((b, i) => ({ ...b, end: out[i + 1]?.y ?? document.documentElement.scrollHeight }));
    });
    for (const b of bands.filter((b) => b.end > b.y)) {
      if (b.id.includes("/")) { console.error(`band shot skipped (id contains "/"): ${b.id}`); continue; }
      await tab.screenshot({ path: `${shots}/${b.id}.png`, fullPage: true,
        clip: { x: 0, y: b.y, width, height: b.end - b.y } });
    }
  } else {
    for (const sec of await tab.locator("[data-section]").all()) {
      await sec.screenshot({ path: `${shots}/${await sec.getAttribute("data-section")}.png` });
    }
  }
  await ctx.close();
}
await browser.close();
```

Screenshots are evidence for the orchestrator's HTML report. Keep them outside the repo, or gitignore them;
a committed screenshot needs a privacy review because text gates cannot read pixels. A band clip's height
only frames the picture. With `BANDS=1`, add `--bands headings` to the gate command below.

## Run the gate

```bash
python3 .claude/skills/deep-code-review/scripts/parity_differ.py --workflow --require-settled \
  --design out/design/home@1440.html --app out/app/home@1440.html \
  --design-tokens design.tokens.json --app-tokens out/app/tokens.css \
  --accept parity-accept.tsv --report out/home@1440.html \
  --design-shots out/design-shots/home@1440 --app-shots out/app-shots/home@1440
```

`--require-settled` turns a marker-free capture (an older one, or the capture script itself failing to
run) into `COULD_NOT_CHECK` too, not only an explicit `data-parity-ready="0"` — drop it only while
migrating captures that predate this signal.
