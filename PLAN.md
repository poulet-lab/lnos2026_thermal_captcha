# Thermal Captcha — Project Plan

> **Status:** Implemented (v1). Hardware validation and event rehearsal still pending.

---

## Context

We are a neuroscience lab studying **temperature perception**. In our research we use
**thermal stimulators (thermodes)** that can change the temperature of the skin very
quickly and precisely. Most of our work is in mice, but for the upcoming **LNOS 2026**
public-outreach event we want to run an interactive demo **with human participants**.

The demo is a thermal perception game we are calling **"Thermal Captcha"** — a playful
nod to the "prove you're human" CAPTCHA challenge: instead of clicking traffic lights,
the person explores their own thermal perception by reporting what they felt on their skin.

- **Hardware:** QST.lab TCS thermode, driven through our own `poulet_py` library
  (the **QST** module: `poulet_py.hardware.stimulator.qst`). "Pulepai" = `poulet_py`.
- **Repo:** `lnos2026_thermal_captcha/` (this repository), a clone of the lab
  `experiment-template`.
- **Setup:** Two screens. A **control/operator screen** driven from the **terminal**
  (a `rich` menu), and a **second screen** facing the person that shows the game
  (title, instructions, green-dot cue, and the six answer images). The participant display
  is built with **Tkinter**.

### The core idea of the game

The person feels a sequence of **temperature traces** on their skin, and after each one
they have to **choose, from six drawn traces, the one that looks like what they just
felt**. It is a forced-choice perceptual matching task dressed up as a fun "captcha".

---

## Aim

Build a robust, easy-to-operate demo that:

1. Is launched and operated **from the terminal** (`rich` menu) — Tkinter is only opened
   once a game actually starts, not on launch.
2. Delivers a well-defined **library of thermal stimulus families** through the TCS
   thermode via `poulet_py`'s QST module.
3. Presents a clean **participant display** on the **second screen** (Tkinter): title,
   instructions, green-dot attention cue, and a six-image forced-choice screen.
4. Uses **pre-generated** schematic trace images (made *before* the event, never during a
   session) as the answer options.
5. **Records** each person's answers and whether they were correct, and can show
   **rankings** (which traces are hardest; how people score).
6. Is **safe** for human skin and reliable enough to run repeatedly with the public.
7. Follows the **lab's existing conventions** (see *Libraries & conventions* below) so it
   feels like the rest of our codebase.

---

## Game flow

### Launch

The operator runs the entry point from the terminal (e.g. `python -m src.experiment.run`),
which shows a **`rich` main menu** (loop until exit):

```
THERMAL CAPTCHA — CONTROL PANEL
  1. Start game
  2. See stimulus-trace ranking      (which traces are hardest / easiest to identify)
  3. See person ranking              (score distribution across people)
  0. Exit
```

### Option 1 — Start game (one person, 10 trials)

1. Operator selects **Start game**. The next **person number** is assigned automatically
   (Person 1, Person 2, …).
2. **Title screen** on the second monitor: big **"Thermal Captcha"** + *"Press Enter to
   start"*.
3. **Instructions screen**: *"When you see the green dot, pay attention to what you feel
   on your skin through the thermal stimulator. At the end you'll see six images — click
   the drawing that looks most like what you just felt."*
4. **10 trials**, with the 10 stimuli **sampled at random** from the pool. For each trial:
   - **Green dot ON** = attend now → TCS delivers a stimulus (exactly **2 s**).
   - Green dot OFF → show the **six answer images** (drawn traces).
   - The person **clicks** the image matching what they felt.
   - Record the trial: stimulus type + **correct / incorrect**.
5. **End screen**: *"You got **X out of 10** correct!"* plus a **three-bucket** social
   comparison relative to their score X (no bar/position shown, just counts of other
   people):
   - **above:** how many people scored **higher** ((X+1) or more correct),
   - **same:** how many people got the **same** score as you (X),
   - **below:** how many people scored **lower** ((X−1) or less correct).

   e.g. if they got **8/10**: *"12 people got 9 or more correct · 7 people got the same as
   you (8) · 41 people got 7 or less."*

   Counts are computed over **other people only** (the current person is excluded).
   If there are no other players yet, show *"You are the first person to play the game!"*
6. Return to the main menu, ready for the next person.

### Options 2 & 3 — Rankings (shown in the terminal via `rich.Table`)

- **Stimulus-trace ranking:** a table of stimulus traces **by name**, showing the **raw
  count** of people who identified each one correctly — **not normalized** by how often it
  was shown. Just "how many people got this one right".
- **Person ranking:** the distribution of scores (how many people got each score 0–10),
  which also powers the end-screen three-bucket (above / same / below) comparison.

---

## Stimulus families

Common constraints for all families:

- **Baseline:** 32 °C (held between stimuli).
- **Duration:** every stimulus is **exactly 2 s**.
- **Amplitudes:** 1, 2, 5, and 10 °C, in both **positive** (warming) and **negative**
  (cooling) directions, unless noted otherwise.
- Each stimulus has a **name** in `lowercase_with_underscores` (e.g. `pulse_pos_5`,
  `slow_up_fast_down_neg_2`) used as the stimulus-type identifier everywhere (data,
  filenames, rankings).

| # | Family | Description | Amplitudes | Notes |
|---|--------|-------------|------------|-------|
| 0 | **Flat / null** | No change — flat line at 32 °C for 2 s. | n/a | Catch trial. |
| 1 | **Pulse** | Fast rise to target, hold, fast return. | ±1, ±2, ±5, ±10 | Symmetric fast on/off. |
| 2 | **Slow ramp up → fast drop** | Slow ramp that reaches the peak at **t = 2 s**, then a fast return to baseline. | ±1, ±2, ±5, ±10 | Ramp rate set so peak lands at 2 s. |
| 3 | **Fast rise → slow decay** | Fast rise (~300 °C/s), then a slow return timed so the temperature is back at baseline at **t = 2 s**. | ±1, ±2, ±5, ±10 | Return rate ≈ amplitude / 2 (see mapping). |

> Direction note: "positive" = warmer than 32 °C, "negative" = cooler than 32 °C.
> e.g. a +10 pulse goes to 42 °C; a −10 pulse goes to 22 °C.
>
> **Oscillation families are deferred** — see *Future ideas / later* at the bottom.

---

## How families map onto the TCS device (important)

A single TCS trigger (`TCSStimulus` → `TCS.trigger()`) produces **one** profile shape:

```
baseline ── ramp at rise_rate ──> target ── hold for `duration` ──> return at return_speed ──> baseline
```

Relevant `TCSStimulus` parameters (`poulet_py/poulet_py/stimulus/tcs.py`):
`baseline`, `target`, `rise_rate` (°C/s), `return_speed` (°C/s), `duration` (ms),
`surface`.

This means all **current** families are expressible as a single trigger:

- ✅ **Flat (0):** target = baseline (or simply don't trigger).
- ✅ **Pulse (1):** high `rise_rate`, short `duration`, high `return_speed`.
- ✅ **Slow-up/fast-down (2):** `rise_rate` chosen so the ramp takes ~2 s (`rise_rate ≈
  amplitude / 2 s`), minimal `duration`, high `return_speed`.
- ✅ **Fast-up/slow-down (3):** `rise_rate = 300 °C/s` (near-instant rise, ~`amplitude/300`
  s), then a slow `return_speed` sized so the descent ends at baseline at t = 2 s:
  `return_speed = amplitude / (2 s − amplitude/300)` ≈ `amplitude / 2` °C/s. Verify against
  the recorded trace.

> Oscillation would NOT be expressible as a single trigger (no arbitrary-waveform upload in
> the command set). That's why it's deferred — see *Future ideas / later*.

---

## Data & storage schema

Persons are labelled **"Person 1", "Person 2", …** on screen (never "participant"). In the
data, `person` is a plain **integer** column starting at **1** and incrementing — simplest,
consistent, and scales without padding decisions. The next number is derived from the max
`person` already in the data.

**Recommended (long format)** — one row per trial, in a single cumulative CSV that grows
across the whole event (`data/raw/responses.csv`):

| column | example | meaning |
|--------|---------|---------|
| `timestamp` | `2026-06-01T17:30:12` | trial time (ISO) |
| `person` | `3` | person number |
| `trial` | `7` | trial index 1–10 |
| `stimulus_type` | `pulse_pos_5` | the delivered stimulus name |
| `chosen` | `slow_up_fast_down_pos_5` | the image the person clicked |
| `correct` | `true` | `chosen == stimulus_type` |

This long format makes both rankings trivial to compute (group by `stimulus_type` for the
trace ranking; group by `person` for the score distribution).

> **Decision: store long.** The wide layout (`person`, then `stimulus_1 … stimulus_10`) is
> just a one-line pivot of this table whenever a per-person view is wanted.

Pre-generate everything **before** the event: the **six answer images** (schematics) are
rendered ahead of time and only displayed during the game — never generated live.

---

## Schematics (answer images)

- One **schematic figure per stimulus trace**: plain **black line**, **dashed gray**
  baseline line, **no axes / no ticks / no frame**. Saved to `reports/stimulus_traces/`.
  All schematics share a **fixed y-range** (32 ± 10 °C plus margin) so amplitudes are
  visually comparable.
- **The six answer images per trial = the correct trace + 5 random traces drawn from the
  entire pool** of pre-generated traces (sampled without replacement, randomized order).
  So every distinct trace (family × amplitude × direction) is a separate, equally-valid
  answer option — the person is matching the *specific* trace they felt, not just the shape
  family.

---

## Libraries & conventions (lab best practices)

Derived from `adaptingtemperatures_gonogo_mice` and `corebodytemp_thermalring`. Match these
so Thermal Captcha feels like the rest of the codebase.

### Libraries
- **`poulet_py[qst]`** — TCS thermode control (`from poulet_py import TCS, TCSStimulus`).
- **`rich`** — all terminal UI: `Console`, `console.rule("[bold cyan] …")`,
  `console.print("[purple]1.[/purple] …")`, `rich.prompt.Prompt.ask`, `Confirm.ask`.
  The numbered menu loop in `gonogo_mice/src/experiment/run.py::display_main_menu` is the
  pattern to copy.
- **`tkinter`** — participant display on the second monitor (open only when a game starts).
- **`matplotlib`** — pre-render the schematic trace images.
- **`python-dotenv`** — load config (e.g. TCS serial port) from a `.env` via
  `find_dotenv()` / `load_dotenv()`.
- **`pathlib`** — paths everywhere; `ROOT_PATH = Path(__file__).resolve().parents[N]`.

### Entry point & structure
- Single entry point at `src/experiment/run.py` with `main()` guarded by
  `if __name__ == "__main__":`, wrapped in `try/except` that calls `log_error(...)` and
  re-raises (see thermalring `run.py`). Run with `python -m src.experiment.run`.
- Keep experiment code under `src/experiment/`; analysis under `src/analysis/`.
- **Adaptation for a public event:** we do *not* need the mice-manager / Brainstem-upload
  machinery from those repos. Keep it lightweight — local files only.

### Logging & saving (copy `thermalring/src/experiment/session_log.py`)
- **Session log:** append rows to `data/other/logs/sessions.csv` with columns
  `timestamp,event,script,message`; call `log_script_event("start"/"end", "run")`.
- **Errors:** also write a per-error TXT with the full traceback to `data/other/logs/`.
- **CSV writing:** `csv.DictWriter`, write the header only if the file is new, open in
  append mode with `encoding="utf-8"`.
- **metadata.json:** canonical `{raw, processed, analyzed}` buckets, written **atomically**
  (temp file + `shutil.move`) — see thermalring `metadata.py`.
- **Timestamps:** ISO `%Y-%m-%dT%H:%M:%S` in data; `%Y%m%d_%H%M%S` for filenames.

### Safety / robustness
- Handle **Ctrl+C** gracefully (signal handler) so the thermode is always closed cleanly
  on exit (pattern in gonogo `run.py::signal_handler`). Always close `TCS` in a `finally`.

---

## History

- **2026-06-01** — Repo `lnos2026_thermal_captcha` created from the lab
  `experiment-template` (standard `data/ notebooks/ reports/ src/` layout, empty
  `logbook.csv`). Requirements gathered verbally; this plan drafted, then expanded with the
  full game flow, terminal menu, six-image forced choice, data schema, and lab conventions.

---

## Steps (proposed)

> Ordered, but expect to iterate. Check items off as they are completed.

### Phase 0 — Setup & de-risking
- [x] Confirm `poulet_py` install with the QST extra (`pip install poulet_py[qst]`) and
      that the TCS connects over serial (port from `.env`). *(Hardware check pending on your
      machine — mock mode works.)*
- [x] Define **human-safety limits**: set `maximum_temperature` and confirm cold limits
      (see Gotchas / Safety). *(Default 45 °C in `.env`; adjust before event.)*
- [x] Scaffold `src/experiment/run.py` with the `rich` main menu (options 1/2/3/0) and copy
      `session_log.py` + `metadata.py` conventions.

### Phase 1 — Stimulus library
- [x] Implement a data-driven stimulus-definition module building the full family ×
      amplitude × direction grid (families 0–3) as named `TCSStimulus` objects, 2 s timing
      baked in.
- [ ] Verify each delivered profile by recording the TCS temperature trace and comparing to
      the intended shape. *(Requires real thermode.)*

### Phase 2 — Schematics (pre-generated answer images)
- [x] Generate one schematic per stimulus trace (black line, dashed-gray baseline, no axes)
      into `reports/stimulus_traces/`. These are the answer images.
- [x] Decide the six-image set rule (fixed categories vs. per-trial distractors).
      *(Correct + 5 random from pool.)*

### Phase 3 — Participant display (Tkinter, second monitor)
- [x] Fullscreen Tkinter window on the **second monitor**.
- [x] Screens: title ("Thermal Captcha" + Press Enter), instructions, **green-dot** cue,
      **six-image clickable** choice screen, end/score screen with social-comparison line.

### Phase 4 — Game loop & control
- [x] Wire **Start game**: assign person number → run 10 trials (green dot → TCS trigger →
      six-image choice → record correct/incorrect) → end screen.
- [x] Sync green-dot timing to the actual TCS trigger (not a bare `sleep`).

### Phase 5 — Data & rankings
- [x] Append each trial to `data/raw/responses.csv` (long format).
- [x] Implement **stimulus-trace ranking** and **person ranking** (`rich.Table`), and the
      end-screen three-bucket comparison.

### Phase 6 — Polish
- [x] Graceful Ctrl+C / thermode cleanup; dry-run rehearsal end-to-end on the real
      two-screen + thermode setup. *(Ctrl+C handler in place; full hardware rehearsal
      pending.)*

---

## Gotchas & things to bear in mind

### Technical
- **2 s means different things per family.** For the slow-ramp family the *rise* takes 2 s;
  for the fast-rise/slow-decay family the *decay* is the slow part. Be explicit in code
  about which segment the 2 s refers to.
- **Rate ↔ amplitude coupling.** To make the slow ramp reach its peak at exactly 2 s, the
  rise rate must scale with amplitude (`rate ≈ amplitude / 2`). Confirm this is the
  intended feel.
- **TCS profile is set by commands** (`commands.py`): `N` baseline, `C` target, `V` rise
  rate, `R` return speed, `D` duration, `S` surface. Units are 0.1 °C and 0.1 °C/s; the
  `TCSStimulus` wrapper handles the scaling.
- **Second-monitor Tkinter** needs explicit geometry/offset to land fullscreen on the
  correct display; verify on the actual event hardware.
- **Timing/threading:** `TCS.trigger()` spawns a background timer thread; the acquisition
  thread streams temperatures at ~100 Hz during stimulation. Coordinate the green-dot
  timing with the actual trigger.
- **Pre-render schematics**, never during a session (avoids latency/jank in front of the
  public).

### Safety (humans!)
- ⚠️ Skin is not mouse skin and this is the **public**. Set `maximum_temperature`
  conservatively. A +10 stimulus from 32 °C reaches **42 °C** — near warmth/heat-pain
  threshold (~45 °C). Confirm the maximum allowed warm target and coldest allowed target
  are comfortable and safe.
- Have a clear, immediate **abort / halt** path for the operator (device `HALT_STIMULATION`).
- Consider hygiene between people (shared thermode surface).

### Process
- **Folder name is `lnos2026_thermal_captcha`** ("captcha", not "capture") — keep naming
  consistent. Always say "Person N", not "participant".
- Keep the stimulus library **data-driven** (one definition of the grid) so schematics,
  delivery, the answer images, and logging all read from the same source of truth.

---

## Decisions (resolved)

- **Person numbering:** plain integer `person` starting at 1 (next = max + 1), displayed
  "Person N". No zero-padding.
- **Storage:** long format (one row per trial); pivot to wide only for display.
- **Trial selection:** the 10 stimuli per person are sampled **at random** from the pool.
- **Six answer images:** correct trace + 5 random traces from the whole pool.
- **Display flow:** traces are shown **only** at the six-image choice step (no preview).
- **Score comparison:** counts **exclude the current person**; compare against everyone
  else who has played. First player gets a dedicated message instead of buckets.
- **Enter key:** all in-game Enter steps (start, after instructions, after results) are
  handled on the **Tkinter display**, not the terminal.
- **Second monitor:** borderless window placed via Win32 `SetWindowPos` (no `-fullscreen`).
- **Family 3 decay:** fast rise at ~300 °C/s, then `return_speed = amplitude/(2 − amplitude/300)`
  (≈ amplitude/2 °C/s) so it returns to baseline at t = 2 s.

No open questions outstanding for the current scope. (Oscillation reference code still
welcome for the deferred families — see below.)

---

## Future ideas / later (out of scope for now)

- ⚠️ **Oscillation families** (oscillate around baseline; step to an offset then oscillate
  with ~1 °C amplitude). **Not** expressible as a single TCS trigger — there is no
  arbitrary-waveform upload in the command set, so these would need command-streaming or a
  firmware waveform mode. Reference oscillation code may be provided later. **Parked for a
  future version.**

---

## Log

- **2026-06-01 (initial)** — Plan drafted. Explored `poulet_py` QST/TCS interface;
  confirmed the single-profile-per-trigger limitation. Confirmed repo scaffold exists.
- **2026-06-01 (update)** — Major expansion after design conversation: added full game flow
  (terminal `rich` menu → Tkinter screens), the six-image forced-choice mechanism, 10
  trials/person, "Person N" labelling, data schema (long-format `responses.csv`), scoring
  and rankings, and a *Libraries & conventions* section derived from `gonogo_mice` and
  `thermalring` (rich menus, `run.py` entry point, `session_log.py`, atomic `metadata.json`,
  pathlib/dotenv). **Oscillation families deferred** to *Future ideas / later*.
- **2026-06-01 (update 2)** — Resolved the answer-image rule: each trial shows the **correct
  trace + 5 random traces from the whole pool**. End screen now uses a **three-bucket**
  comparison (people who scored higher / same / lower than you). Stimulus-trace ranking is a
  **raw, unnormalized** count of correct identifications per trace, listed by name.
- **2026-06-01 (update 3)** — Closed all open questions: integer person numbering from 1;
  long-format storage; 10 trials sampled at random; comparison counts include the current
  person over everyone; traces shown only at the choice step; Family 3 = ~300 °C/s rise then
  `return_speed = amplitude/(2 − amplitude/300)` to reach baseline at t = 2 s.
- **2026-06-01 (implementation v1)** — Full codebase implemented under `src/experiment/`:
  `stimuli`, `schematics`, `display`, `game`, `run`, `responses`, `rankings`,
  `tcs_controller`, `session_log`, `metadata`, `config`. 25 stimulus schematics generated.
  17 unit tests passing. Entry point: `python -m src.experiment.run`. Mock TCS enabled by
  default via `.env`.
- **2026-06-01 (display fixes)** — Second monitor via borderless window + `SetWindowPos`;
  Enter prompts moved to Tkinter; score comparison excludes current person; first player
  gets special end-screen message; monitor list printed at game start.
