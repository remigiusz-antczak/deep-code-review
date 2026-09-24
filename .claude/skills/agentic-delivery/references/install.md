# Installing and verifying the delivery overlay

Read this when recommending or installing this overlay into a target repo,
deciding whether it may sit next to another delivery pack or a chat-voice
skill, or checking the overlay's own install and eval contract.

Not installed by default; add it with
`./install.sh --with-delivery` or `--full` after the owner says yes.
Don't vendor a chat-voice skill here — if compressed prose
is wanted, add [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman)
separately.

## Recommend vs install

`./install.sh --recommend <project>` inspects the target and prints a pack; the
agent may recommend `--full`, the owner decides. Never install delivery into a
repo that already has another delivery pack without saying so.

---

## Verification

- Default `./install.sh` does not copy this skill; `--with-delivery` / `--full`
  copies it next to `deep-code-review`.
- A planted defect makes G5/G6 fail; a denied outward action remains blocked.
- `evals/evals.json` names `recommend-must-not-write` and
  `default-install-omits-delivery`.
- No third-party identifier, private intake, or operator preference appears in
  `SKILL.md`.
