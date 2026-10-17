# Canon — the live lore base

`mechanisms.jsonl` holds the hard-science mechanism cards (`physics.md`), validated the same way: cited, append-only, postulates from the closed list, budgets computed. It starts with the ship's core systems and grows case by case, as the world relies on more.

`cards.jsonl` is the lore baseline: short reference cards in our own words, each citing where it was verified. It grows from verified lore checks and never changes silently.

## A card

One JSON object per line:

```json
{"id": "K-014", "layer": "rules", "topic": "transporters and shields",
 "statement": "A transporter can't beam through a raised deflector shield; shields have to drop for a lock.",
 "sources": ["https://memory-alpha.fandom.com/wiki/Transporter"],
 "verified_at": "2026-10-18", "supersedes": null}
```

- **`layer`**:
  - `rules`: how the universe works (physics, technology, institutions, what species and canon people *are*). Invariant; the branch can't change it.
  - `history-pre`: events before the branch (stardate 41153.7). Fixed.
  - `history-post`: canon's events after the branch. **Not** binding: it's the default trajectory, used only through `forces.md` and checked against the branch's own state and `divergence.json`.
- **`sources`**: at least one. Memory Alpha is the default.
- **`supersedes`**: a correction is a *new* card naming the old one. The validator rejects any edit to an existing line, so the baseline can't drift without a record.
- Statements are paraphrased, never quoted, and kept short.

## Checking lore, at any time

```
python3 tools/wk.py lore worlds/enterprise "what you are about to rely on"
```

This searches the cards, `law.md`, the world's precedents and its divergences, and says whether coverage is solid, thin or none. With no solid coverage, the GM spawns a fresh lore agent (`modules/eval/LORE_AGENT.md`), whose verified answer becomes a new card. Every turn that introduces something lore governs records it in `lore_touch`, with a `LORECHECK` for each item (`STATE.md`).

## Verdicts

- `consistent`: matches canon rules and history (or the branch's history, after the branch).
- `diverged`: differs from canon's post-branch history, with a valid chain in `divergence.json` back to something somebody actually did. Correct, and expected.
- `unsupported`: canon is silent. It stands as an [assumed] precedent with its reasoning, and Will may overrule it.
- `contradicts`: breaks a rule, or differs from canon's history with no chain. That's drift: correct it.
