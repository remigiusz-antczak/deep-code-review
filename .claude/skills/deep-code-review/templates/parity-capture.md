# Parity capture contract (template)

Copy this into the target repo and fill in the placeholders. It defines how both renders (design and app)
are exported for `scripts/parity_differ.py` so that the comparison runs on populated, signed-in, same-state
pages. Nothing here runs in CI: the snippet is a template for the project's own harness.

## What each capture must produce

For every page in the correspondence table, at every viewport in the list below, on **both** sides:

1. `<out>/<side>/<page>@<width>.html` is a DOM snapshot after the page settles. Every section root carries
   `data-section="<id>"` (the same ids on both sides), and populated units carry `data-item`.
2. **Computed styles.** Every visible text-bearing element that should be style-checked carries a
   `data-cs` JSON object with a non-empty value for each property the differ compares (`font-family`,
   `font-size`, `font-weight`, `line-height`, `letter-spacing`, `color`, `background-color`, `padding`,
   `border-radius`, `box-shadow`). Values come from `getComputedStyle`, exported in the same browser for
   both sides.
3. **Visibility markers.** Every element whose class hides it through a stylesheet (`hidden`, `sr-only`,
   `invisible`, `d-none`, `visually-hidden`) carries `data-visible="true"` or `"false"`, read from
   `checkVisibility()`.
4. Optional section screenshots: `<out>/<side>-shots/<page>@<width>/<section id>.png`. Pass that folder
   to `--design-shots` / `--app-shots` together with `--report`.

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
  await tab.goto(url, { waitUntil: "networkidle" });
  await tab.evaluate((props) => {
    for (const el of document.querySelectorAll("[data-section] *")) {
      if (/\b(hidden|sr-only|invisible|d-none|visually-hidden)\b/.test(el.getAttribute("class") || "")) {
        el.setAttribute("data-visible", String(el.checkVisibility()));
      }
      const own = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
      if (own && el.checkVisibility()) {
        const cs = getComputedStyle(el);
        el.setAttribute("data-cs", JSON.stringify(Object.fromEntries(props.map((p) => [p, cs.getPropertyValue(p)]))));
      }
    }
  }, PROPS);
  mkdirSync(`out/${side}`, { recursive: true });
  writeFileSync(`out/${side}/${page}@${width}.html`, await tab.content());
  const shots = `out/${side}-shots/${page}@${width}`;
  mkdirSync(shots, { recursive: true });
  for (const sec of await tab.locator("[data-section]").all()) {
    await sec.screenshot({ path: `${shots}/${await sec.getAttribute("data-section")}.png` });
  }
  await ctx.close();
}
await browser.close();
```

Screenshots are evidence for the orchestrator's HTML report. Keep them outside the repo, or gitignore them;
a committed screenshot needs a privacy review because text gates cannot read pixels.

## Run the gate

```bash
python3 .claude/skills/deep-code-review/scripts/parity_differ.py --workflow \
  --design out/design/home@1440.html --app out/app/home@1440.html \
  --design-tokens design.tokens.json --app-tokens out/app/tokens.css \
  --accept parity-accept.tsv --report out/home@1440.html \
  --design-shots out/design-shots/home@1440 --app-shots out/app-shots/home@1440
```
