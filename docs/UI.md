# The web UI

The interface is styled as a cyberpunk "hacker terminal" (SPAM//SCAN v2). It's plain Jinja2 templates with inline CSS, JavaScript and SVG: no frameworks, CDNs, web fonts or audio files.

← Back to the [README](../README.md) · See also [API.md](API.md) for the endpoint the UI calls

<img src="images/threat-matrix-gray.png" alt="Scanner and Threat Matrix with the Gray zone drawer open" width="820">

## Contents

- [Layout](#layout)
- [Scanning a message](#scanning-a-message)
- [Verdict characters: skull, angel, ghost](#verdict-characters)
- [Reading the result](#reading-the-result)
- [Threat Matrix](#threat-matrix)
- [Gray zone](#gray-zone)
- [Random Payload and the R key](#random-payload-and-the-r-key)
- [Sound effects](#sound-effects)
- [Deep links: ?q= and ?open=](#deep-links)
- [Boot sequence and Matrix rain](#boot-sequence-and-matrix-rain)
- [Accessibility and reduced motion](#accessibility-and-reduced-motion)
- [The How it works page](#the-how-it-works-page)
- [Customising](#customising)

## Layout

| Area | What it shows |
|---|---|
| Header | ASCII-art `SPAM//SCAN` logo (a compact logo on narrow screens), the `[ SFX: ON/OFF ]` toggle and the `[ how_it_works ]` link |
| Status line | `model: tfidf+logreg · datasets: 7 · acc: 98.1% · rules: 15+8 · lang: en / hinglish / हिंदी`. The numbers come live from `metrics.json` and the rule lists |
| Input card | The message box (up to 10,000 characters, with a live character count), `[ EXECUTE SCAN ]`, and the scan log and result |
| Threat Matrix | 18 category tiles with an expandable drawer of example messages |
| Footer | Model description, held-out accuracy and F1, SMS and e-mail F1, and a link to the details |

## Scanning a message

1. Paste an SMS or e-mail and press **[ EXECUTE SCAN ]**, or press <kbd>Ctrl</kbd>/<kbd>⌘</kbd> + <kbd>Enter</kbd> in the text box.
2. The button changes to `[ SCANNING… ]`, a neon scan bar runs, and a **terminal log** prints the steps (`tokenizing…`, `normalizing urls / phones / money / numbers…`, `vectorizing…`, `running model…`). The first few lines are paced for effect. The last lines show the real results: `p(spam)`, the red flags detected (pink), whether a safe signal was applied or blocked (yellow), and the verdict.
3. The result card appears. The verdict title gets a brief RGB-split **glitch**, and the reason is **typed out** like a terminal. Click the reason to finish typing at once. Screen readers get the full text immediately (see [Accessibility](#accessibility-and-reduced-motion)).

## Verdict characters

Each verdict has its own original inline-SVG character in the same slot, left of the verdict. On phones (≤ 480 px wide) it shrinks and sits beside its caption.

<table>
<tr><th>Spam: skull</th><th>Not spam: angel</th><th>Unsure: ghost</th></tr>
<tr>
<td><img src="images/mobile-spam-skull.png" alt="Skull character for Spam" width="220"></td>
<td><img src="images/mobile-notspam-angel.png" alt="Angel character for Not spam" width="220"></td>
<td><img src="images/mobile-unsure-ghost.png" alt="Ghost character for Unsure" width="220"></td>
</tr>
<tr>
<td>Neon magenta skull with a cyan crack. It flickers in, then flickers now and then. Caption <code>!! THREAT DETECTED !!</code></td>
<td>Floating cyan and green angel with wings, a pulsing yellow halo and sparkles. Caption <code>// ALL CLEAR //</code>. Shown for every Not-spam variant, including standard alerts</td>
<td>Wobbling yellow ghost with a magenta question mark and an occasional glitch. Caption <code>?? ANALYSIS INCONCLUSIVE ??</code>. The CSS class is <code>.phantom</code>, because <code>.ghost</code> is already used by the Random Payload button</td>
</tr>
</table>

The characters are decorative (`aria-hidden="true"`). The verdict text carries the meaning.

## Reading the result

- **Verdict box.** `SPAM`, `UNSURE`, `NOT SPAM` or one of the variants (`NOT SPAM (STANDARD ALERT + OFFICIAL LINK)`, `UNSURE (LOOKS LIKE A STANDARD ALERT)`, …), plus the reason. Pink means spam, yellow unsure and green not spam.
- **ml_model.score.** The ML probability with a neon meter. The meter's background shows the three zones (green < 35%, yellow 35–65%, pink ≥ 65%), and a white pin marks the score.
- **red_flags (rules).** One card per rule that fired, with its title, its explanation and the exact `matched:` snippets. High rules are pink and medium rules yellow. If none fired: `[ok] no red flags found.`
- **safe_signals.** Green `[+]` cards when a standard-alert signal applied. Grey `[-] … (not applied)` cards when it matched but was blocked, plus a "Why the safe signal was not applied" list. If none matched: `[--] doesn't look like a standard transactional alert.`
- **why: tokens that moved the ML score.** Your message with each word highlighted pink (towards spam) or green (towards not spam). Brighter means stronger, and hovering shows the exact contribution. Underneath is the arithmetic. For `You have wo 1 million dollars` it reads `score = base -3.29 + feature contributions +5.72 = 2.43 → 91.9% after the sigmoid`.
- **Top spam-leaning / safe-leaning features.** Up to 8 each, with bars and signed contributions. Character n-grams show which word they came from (`lars in "dollars"`).

How these numbers are computed is explained in [ARCHITECTURE.md](ARCHITECTURE.md#explanations-and-highlighting).

## Threat Matrix

The gallery is a grid of **18 tiles**, one per category in `examples.json` (83 messages in total). It replaced an earlier scrolling list of examples, and nothing needs scrolling inside it. The grid has 2 columns on phones, then 3, 4 and 6 as the screen gets wider.

Each tile shows a **code and icon**, the category name, a **level badge**, a **score** and a progress bar. Hovering a tile gives a tooltip with both ML-only and final scores.

| Tile | Category (`id`) | Examples | Level | ML alone | Final |
|---|---|---:|---|---:|---:|
| 💸 UPI | UPI / payment phishing (`upi`) | 5 | MED | 4/5 | 5/5 |
| 🏦 KYC | KYC expired, bank / telecom (`kyc`) | 7 | HIGH | 5/7 | 7/7 |
| 📦 PKG | Fake courier / parcel fee (`courier`) | 4 | MED | 3/4 | 4/4 |
| 🚔 ARR | Digital arrest extortion (`arrest`) | 4 | MED | 3/4 | 4/4 |
| ☎️ CALL | Fake customer care (`care`) | 3 | LOW | 3/3 | 3/3 |
| 👔 BEC | CEO fraud / BEC (`bec`) | 4 | CRIT | 1/4 | 4/4 |
| 💼 JOB | Fake job / work-from-home fee (`job`) | 4 | MED | 3/4 | 4/4 |
| 🆘 SOS | Emergency / vishing money request (`emergency`) | 4 | CRIT | 0/4 | 4/4 |
| 🎰 LOT | Prize / lottery (`prize`) | 5 | HIGH | 3/5 | 5/5 |
| 📈 INV | Investment / crypto / trading tips (`invest`) | 4 | LOW | 4/4 | 4/4 |
| 💳 LOAN | Loan app / instant loan (`loan`) | 4 | LOW | 4/4 | 4/4 |
| ⚡ PWR | Electricity bill disconnection (`electricity`) | 3 | CRIT | 1/3 | 3/3 |
| 💔 SXT | Sextortion / romance / dating (`romance`) | 4 | HIGH | 2/4 | 3/4 |
| 🧾 TAX | Tax refund / income tax (`tax`) | 3 | LOW | 3/3 | 3/3 |
| 🚨 KID | Family kidnap / virtual kidnapping (`kidnap`) | 4 | HIGH | 2/4 | 4/4 |
| 👑 419 | Nigerian prince / advance-fee (`advancefee`) | 4 | LOW | 4/4 | 4/4 |
| ✅ SAFE | Genuine messages (`genuine`) | 9 | SAFE | 3/9 | 7/9 correct |
| 👻 ??? | Gray zone / Unsure (`gray`) | 8 | GRAY | n/a | 8/8 still unsure |

*(These are the current values. They are recomputed every time the server starts.)*

- **Level** shows how often the **ML model alone** misses that category's examples: `LOW` = misses none, `MED` = catches ≥ 75%, `HIGH` = ≥ 50%, `CRIT` = < 50%. It's computed, not hand-set. The `genuine` tile is always `SAFE` (green) and the Gray zone is always `GRAY` (yellow).
- **caught x/y** counts the **final verdict**, after the rules. The SAFE tile says `correct x/y` and the Gray tile says `unsure x/y`.

**The drawer.** Click a tile and a terminal-style drawer (`root@spamscan:~$ cat payloads/kyc.txt`) opens **below that tile's row**, spanning the full width. Each line shows:

- a language tag: `[EN]`, `[HI-EN]` (Hinglish), `[HI]` (Devanagari) or `[TYPO]` (misspelled);
- a short label;
- the ML probability;
- the final verdict: `SPAM`, `OK` or `UNSURE`, with a magenta **✗** if it differs from the example's `expected` label.

**Click a line to scan that message.** Click the tile again, press `[x]` or press <kbd>Esc</kbd> to close the drawer. Opening a tile with the keyboard (<kbd>Enter</kbd>/<kbd>Space</kbd>) moves focus to the first line. The drawer moves to the right row when the window is resized.

All numbers, links and names in the gallery are fake placeholders (`98XXXXXX12`, `*.top`, `*.xyz`, example domains).

## Gray zone

The yellow **`???` tile** collects **borderline messages that land in Unsure**, the ones that summon the ghost. Each one is "correct" when it **stays** in Unsure. It currently holds 8:

| Message | ML P(spam) | Why it's Unsure |
|---|---:|---|
| Payment failed (`Your Netflix payment failed. Update your payment method…`) | 42% | Borderline ML, no rule |
| Wedding photos link (Hinglish, `bit.ly/…`) | 5% | Medium `suspicious_link` with low ML |
| Refund link (typos, `refund-xxxx.xyz`) | 17% | Medium link rule with low ML |
| Insurance renewal nudge | 52% | Borderline ML, no rule |
| Update account details | 47% | Borderline ML, no rule |
| Genuine HDFC debit alert (no link) | 100% | Safe signal, but ML ≥ 95% |
| Genuine UPI sent alert | 98% | Safe signal, but ML ≥ 95% |
| Official link, but a hard-sell promo (`flipkart.com`) | 99% | Official link only, ML ≥ 95% |

It's an honest showcase of where the system hesitates. Genuine alerts are in here on purpose: see [Limitations](../README.md#limitations).

## Random Payload and the R key

**`[ RANDOM PAYLOAD ]`** (top right of the Threat Matrix) picks a random line from **all** gallery categories, including genuine and Gray-zone messages. It loads the line into the input, scrolls up and scans it.

Pressing <kbd>R</kbd> anywhere on the page does the same. The shortcut is ignored while you're typing in the text box or another input, and when <kbd>Ctrl</kbd>, <kbd>⌘</kbd> or <kbd>Alt</kbd> is held, so <kbd>Ctrl</kbd>+<kbd>R</kbd> still reloads.

## Sound effects

Short synthesised sounds are made with the **Web Audio API**. There are no audio files.

| Event | Sound |
|---|---|
| Scan starts, or SFX switched on | Two quick high square-wave blips |
| **Spam** | A burst of filtered noise and a falling, detuned sawtooth "alarm", played twice |
| **Not spam** | Two rising sine notes (a friendly "ding-ding") |
| **Unsure** | One soft triangle-wave tone |

- They're **on by default**, but browsers only allow sound after you interact with the page. Nothing plays until your first click or key press.
- Toggle them with **`[ SFX: ON ]` / `[ SFX: OFF ]`** in the header. The choice is saved in your browser's `localStorage` under the key `sfx`.

## Deep links

| URL | Effect |
|---|---|
| `/?q=<url-encoded text>` | Fills the input and **scans immediately**. The boot animation is skipped. For example: `http://127.0.0.1:5000/?q=u%20won%201%20milion%20dolars` |
| `/?open=<category id>` | Opens that Threat Matrix drawer. For example `/?open=gray`, `/?open=kyc` or `/?open=advancefee`. The ids are listed in the table above |

Both can be combined: `/?open=bec&q=…`. Remember that `?q=` puts the message in the URL, which means browser history and the server log.

## Boot sequence and Matrix rain

- **Boot sequence.** On the first visit in a browser session, a short (about 1 second) terminal boot screen prints the real feature count, rule counts and number of datasets, then fades out. Click or press any key to skip it. It's shown once per session (`sessionStorage`) and never for `?q=` deep links.
- **Matrix rain.** A faint full-screen canvas of falling katakana, digits and symbols in cyan, green and occasionally magenta. It runs at about 18 fps and pauses when the tab is hidden.

Both live in `templates/fx.html` and are shared by both pages.

## Accessibility and reduced motion

- **`prefers-reduced-motion: reduce`.** The boot screen and Matrix rain are not shown, all CSS animations and transitions are switched off, the glitch effect is skipped, the reason appears instantly instead of being typed, the scan log is not paced, and scrolling is instant. The skull, angel and ghost **stay still** but remain visible.
- **`prefers-contrast: more`.** The scan-line and noise overlays are hidden and muted text is brightened.
- **Screen readers.** There is a visually hidden `<h1>`. The full verdict reason is announced through a polite live region (`How this was decided: …`), even while the visual typewriter is running. Decorative art is `aria-hidden`, tiles use `aria-expanded` and `aria-controls`, and the drawer is a labelled region.
- **Keyboard.** All controls are real buttons with a visible yellow focus outline. <kbd>Ctrl</kbd>/<kbd>⌘</kbd>+<kbd>Enter</kbd> scans, <kbd>R</kbd> picks a random payload, and <kbd>Esc</kbd> closes the drawer and returns focus to the tile.

## The How it works page

`/how-it-works` is generated from `metrics.json`, `redflags.py` and `domains.py`, so it is always in sync with the running model.

<img src="images/how-it-works.png" alt="The how-it-works page" width="700">

1. **The two independent parts.** The ML model, the red-flag rules, the safe signals, the official-domain check, and the verdict steps with the live thresholds.
2. **Training data.** Each dataset with its link, type and counts.
3. **Held-out test results.** Accuracy, precision, recall and F1 per dataset and per group.
4. **Robustness probes.** ML-only and ML + rules per group. Expanding a group lists its misses.
5. **Strongest features overall.** The top 20 towards spam and towards not spam, for all features and for words/phrases only.
6. **Red-flag rules.** Every rule with its severity badge, id and explanation, plus notes on the two forms of the KYC rule and how domains are matched.
7. **Safe signals.** Every signal, the blockers, an "⚠️ scammers may imitate this format" warning, and an expandable list of all **96 official domains**.
8. **Known limitations.**

## Customising

- **Add gallery examples.** Edit `examples.json`: `{"label", "lang": "English|Hinglish|Hindi|Misspelled", "expected": "spam|ham|unsure", "text"}` inside a category `{"id", "title", "icon", "code", "examples": [...]}`. Restart the app so the tile statistics are recomputed. Use fake numbers and links only.
- **Colours** are CSS variables in `templates/base_style.html` (`--cyan`, `--magenta`, `--yellow`, `--spam`, `--ham`, …).
- **Unsure band.** `UNSURE_LOW` and `UNSURE_HIGH` in `explain.py`. The meter and the How it works page read them automatically.
