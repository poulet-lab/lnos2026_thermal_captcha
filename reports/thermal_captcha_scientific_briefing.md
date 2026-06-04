# Thermal Captcha — scientific briefing for thermo-tactile consultation

**Document purpose.** This note describes an interactive thermal-perception game we built for a public outreach event. We are **not** claiming it is a controlled psychophysical experiment. We would like your expert view on: (1) whether similar paradigms exist in the thermo-tactile literature; (2) what perceptual mechanisms the task might tap; and (3) how the game could be redesigned into a proper experiment.

**Audience.** Scientists working on human thermo-tactile sensation, thermal detection/discrimination, dynamic thermal stimulation, and related psychophysics.

**Repository.** `lnos2026_thermal_captcha` (Poulet lab, neuroscience / temperature perception).

---

## 1. Background and motivation

Our lab studies temperature perception (primarily in mice). For **LNOS 2026**, a public science event, we wanted a hands-on demo that lets visitors **feel** precisely controlled thermal waveforms on the skin and report what they perceived — framed as a playful game called **“Thermal Captcha”** (a nod to CAPTCHA “prove you're human” tasks).

The demo is meant to be:

- Safe and repeatable with untrained members of the public
- Operable by a single experimenter from a laptop
- Engaging enough for a booth setting
- Informative about how rich thermal sensations can be beyond “hot” vs “cold”

We have **no settled hypothesis** about the scientific value of the current format. The game collects behavioural data opportunistically during the event, but we have not pre-registered analyses or designed it to isolate specific perceptual dimensions.

---

## 2. What the participant does (task overview)

Each person plays **one session of 10 trials**. The flow on each trial is:

1. **Round cue** — full-screen bilingual text: *“Runde X von 10” / “Round X of 10”* (~1 s).
2. **Attention cue** — a green dot appears on a second monitor; the participant is instructed to attend to the thermode on their skin.
3. **Thermal delivery** — a programmed temperature trace is delivered through a contact thermode (~2 s; see §4).
4. **Attention cue off** — green dot disappears.
5. **Forced choice** — six **pre-drawn schematic temperature traces** (PNG images) are shown; the participant clicks the drawing that “looks most like what you just felt.”
6. **Round cue again** — same round number shown for ~1 s, then the next trial (or results after trial 10).

Before the first trial, the participant sees a title screen, bilingual instructions, and a ready screen (all advance on Enter key press from the operator terminal).

**Instructions (substance):** While the green dot is visible, attend to what you feel on your skin through the thermal stimulator. Then choose among six drawings the one that best matches what you felt.

**Scoring:** 1 point per trial where the chosen schematic name matches the delivered stimulus name. At the end, the participant sees their score (X/10) and a coarse social comparison to previous players at the same difficulty level.

There is **no feedback during the game** (no “correct/incorrect” per trial).

---

## 3. Apparatus and stimulation hardware

| Parameter | Value / note |
|-----------|--------------|
| Device | QST.lab **TCS** thermode |
| Control library | In-house `poulet_py` (QST module): `TCS.trigger(TCSStimulus(...))` |
| Stimulation surface | Surface index `0` (single active zone in current config) |
| Baseline temperature | **32 °C** (maintained between trials via `HALT_STIMULATION`) |
| Safety cap | **45 °C** maximum commanded temperature |
| Contact | Participant places skin on the thermode probe (exact body site not standardized in software — typically volar forearm or similar at operator discretion) |
| Displays | Two monitors: operator terminal (Rich CLI menu) + participant fullscreen Tkinter UI on second monitor |

During real-hardware runs, we optionally record **multi-channel temperature traces** from the device buffer (~20 Hz effective logging; device buffer up to ~100 Hz) and save CSV + PNG per trial. This lets us compare **commanded** vs **measured** skin temperature, but these recordings are for QA/calibration rather than participant-facing feedback.

---

## 4. Stimulus space

### 4.1 Global constraints

- **Nominal epoch length:** 2 s for all non-flat stimuli (families differ in how ramp/hold/return are distributed within that window).
- **Amplitudes:** ±1, ±2, ±3, ±5, ±6, ±10 °C relative to 32 °C baseline (37 stimuli total, plus one null).
- **Direction:** “Positive” = warming; “negative” = cooling.
- **Fast ramp rate:** 300 °C/s where a “fast” segment is used.

### 4.2 Stimulus families (temporal profiles)

Each stimulus has a unique name (e.g. `pulse_pos_5`, `slow_up_fast_down_neg_2`) used in data logging and as the filename of its schematic PNG.

| Family | Description | Perceptual intent (informal) |
|--------|-------------|------------------------------|
| **Flat / null** (`flat`) | No thermal change; baseline held ~2 s | Catch / “no change” baseline |
| **Pulse** | Fast rise → brief hold → fast return (symmetric on/off at 300 °C/s) | Square-ish thermal bump |
| **Slow up, fast down** | Slow linear ramp reaching peak at **t = 2 s**, then fast return to baseline | Gradual warming/cooling onset, abrupt offset |
| **Fast up, slow down** | Near-instant rise (~300 °C/s), minimal plateau (~10 ms), slow return timed so temperature is back at baseline at **t = 2 s** | Abrupt onset, gradual offset |

For each family (except flat), we include **both polarities** and **six amplitudes** (±1, ±2, ±3, ±5, ±6, ±10 °C), giving **36 dynamic stimuli + 1 flat**.

The **answer images** shown to the participant are **idealized theoretical traces** (piecewise-linear plots generated from the same parameters), not recordings from the participant’s own trial. All schematics share a fixed y-axis range so amplitude differences are visually comparable.

### 4.3 Mapping to device commands

Each dynamic stimulus is implemented as a **single** `TCSStimulus` trigger:

```
baseline ── rise at rise_rate ──> target ── hold for duration ── return at return_speed ──> baseline
```

Family-specific parameter choices:

- **Pulse:** high rise/return rates; hold duration fills remaining time within ~2 s.
- **Slow up, fast down:** `rise_rate ≈ amplitude / 2 s`; `duration` marks when return begins (at ~2 s).
- **Fast up, slow down:** `rise_rate = 300 °C/s`; return rate sized so return completes at ~2 s.

We have verified on hardware that commanded profiles approximate the intended shapes (calibration runs deliver each stimulus in isolation and log measured temperature).

### 4.4 Difficulty levels (operator-selected)

For the public game, the operator chooses a difficulty **before** each session. This restricts which amplitudes appear in both **delivered trials** and **choice foils**:

| Level | Amplitudes used |
|-------|-----------------|
| Easy | ±5, ±10 °C |
| Medium | ±3, ±6 °C |
| Hard | ±1, ±2 °C |

All three temporal families (plus flat) remain in the pool; only amplitude subsets change. Rankings and end-screen comparisons are computed **within difficulty level**.

---

## 5. Trial design and foils

Per session:

- **10 trials**, stimuli sampled **without replacement from the eligible pool** when possible (resampled with replacement if the pool is smaller than 10 — not an issue at current pool sizes).
- **Six-alternative forced choice (6-AFC):** 1 correct schematic + 5 foils drawn from the same difficulty-filtered pool (excluding the correct answer), positions shuffled.
- Foils can differ in **family**, **polarity**, and/or **amplitude** from the target. There is **no structured foil selection** (e.g. we do not systematically pair “slow up” targets with “fast up” foils).

There is **no inter-stimulus interval control** beyond operator pacing and ~1 s round-progress screens. Baseline is re-established via `HALT_STIMULATION` before each delivery.

---

## 6. Data recorded

Each trial appends one row to `data/raw/responses.csv`:

| Column | Meaning |
|--------|---------|
| `timestamp` | Trial time (local) |
| `environment` | `lnos` (event), `troubleshooting` (lab testing), or `mock_tcs` |
| `difficulty` | `easy` / `medium` / `hard` |
| `person` | Integer session ID (within environment) |
| `trial` | 1–10 |
| `stimulus_type` | Delivered stimulus name |
| `chosen` | Clicked schematic name |
| `correct` | Boolean match |

Aggregated rankings (terminal menu):

- **Stimulus ranking:** count of correct identifications per stimulus name (not normalized by presentation frequency).
- **Person ranking:** score distribution across players.

Optional: per-trial **measured thermal traces** (CSV/PNG) under `data/raw/thermal_traces/`.

---

## 7. What this task is *not* (limitations for interpretation)

We want to be explicit about what the current game **does not** control:

1. **Not a threshold or discrimination study** — no staircases, repetitions, or adaptive procedures.
2. **Low trial count per person** — 10 trials, each stimulus type usually shown at most once per person.
3. **Cross-modal matching** — participants match **felt** thermal events to **seen** line drawings, not to other thermal samples on the same trial.
4. **Idealized foils** — schematics are theoretical, not participant-specific or device-recorded traces; visual similarity may not equal perceptual similarity.
5. **Unbalanced foil sampling** — foils are random, not designed to test specific confusions (e.g. pulse vs slow-ramp).
6. **Unstandardized placement / adaptation** — contact force, skin site, and prior trial history are not recorded.
7. **No individual difference covariates** — age, handedness, thermosensitivity questionnaires, etc. are not collected.
8. **Catch trial rarity** — `flat` is in the pool but may appear rarely in a 10-trial sample.

These choices favour **throughput and engagement** over mechanistic inference.

---

## 8. Informal perceptual hypotheses (ours, unsettled)

We suspect the task may engage several distinguishable abilities, but we have not tested which dominate:

1. **Temporal profile sensitivity** — Can people distinguish slow-onset vs fast-onset envelopes at matched peak amplitude?
2. **Warm vs cool quality** — Is polarity encoded independently of “shape,” or do warming/cooling ramps feel asymmetric even when mirror-symmetric in temperature space?
3. **Amplitude scaling** — At ±1–2 °C, are family differences still identifiable, or does the task become chance-like?
4. **Abstract “trace shape” matching** — Does matching felt heat to a **visual graph** reflect a genuine internal representation of thermal dynamics, or visual metaphor / demand characteristics?
5. **Confusion structure** — Do errors cluster by family (e.g. slow_up vs fast_up) more than by amplitude or polarity?

Event data may allow exploratory confusion matrices, but power per cell will be low.

---

## 9. Questions we would like to ask you

### 9.1 Prior work

- Has anyone published a **human thermo-tactile identification** task for **dynamic temperature waveforms** (beyond simple ramps, pulses, or step changes)?
- Are there close parallels in **vibrotactile** or **nociceptive thermal** literature (temporal pattern identification, “tactile chords,” thermal flutter, etc.) we should cite?
- Is **visual–thermal cross-modal matching** of time–temperature profiles used as a dependent measure, or is it considered methodologically weak?

### 9.2 Perceptual mechanisms

- Which **receptor populations** (CMRs, AMHs, cold fibers) are likely to dominate for our **2 s, 1–10 °C** dynamic stimuli at **32 °C** baseline?
- Do warming and cooling ramps with **mirror-symmetric temperature trajectories** typically yield symmetric percepts, or should we expect strong asymmetries?
- Are our **300 °C/s** “fast” segments likely to produce **impulse-like** sensations distinct from slower ramps, or are they dominated by thermal mass / contact mechanics?
- Is **32 °C** an appropriate neutral baseline for hairy skin / volar forearm in this context?

### 9.3 Stimulus parameters

- Are amplitudes **±1–10 °C** reasonable for supra-threshold identification in untrained visitors, or should public demos stay narrower for comfort and safety?
- Is a fixed **2 s** window sensible for comparing families, or do some profiles need longer integration times to be identifiable?
- Should we expect **adaptation** or **after-sensations** across 10 back-to-back trials to materially bias responses?

### 9.4 Turning this into an experiment

If we wanted peer-reviewable science from this platform, what would you prioritize?

- **Within-subject repeated measures** with many trials per stimulus type (power for d′ / confusion matrices)?
- **Same-modality comparison** (choose which of six **thermal** profiles to replay digitally) vs retained cross-modal schematics?
- **Adaptive staircases** on amplitude or ramp rate for family-specific thresholds?
- **Structured foil sets** to test specific confusions (family × polarity × amplitude)?
- **Blocking vs randomizing** family and amplitude?
- Recording **RT**, **confidence ratings**, or **continuous response** (e.g. drawing the felt trace)?

We can modify software relatively easily: stimulus lists, trial counts, foil algorithms, and data columns are parameterized.

---

## 10. Sketch of possible experimental directions

Below are three paths that seem natural extensions; we welcome your judgment on feasibility and novelty.

### A. Thermal temporal pattern identification

Treat each `(family, polarity, amplitude)` token as a **stimulus class** and estimate **confusion matrices** and **d′** with sufficient repetitions. Primary question: which temporal features (rise time, fall time, peak duration) drive identifiability?

### B. Warm–cool perceptual asymmetry

Within matched temporal envelopes, compare identification accuracy and confusion rates for **+ΔT** vs **−ΔT** at equal absolute amplitude — related to hot–cold fibre contributions and perceived intensity asymmetries.

### C. Cross-modal vs unimodal matching

Compare current **feel → schematic** task to **feel → replayed thermal candidate** (if hardware allows rapid sequential delivery) or **schematic → feel** (visual preview then thermal match). Tests whether visual schematics tap the same internal representation as thermal comparison.

---

## 11. Materials we can share

- Source code for stimulus definitions, game flow, and hardware mapping (`src/experiment/`)
- Pre-generated schematic PNGs (`reports/stimulus_traces/` after running `python -m src.experiment.generate_schematics`)
- Example calibration folders with measured traces (`data/raw/thermal_traces/calibration/`)
- Cumulative response CSV from testing sessions

---

## 12. Summary in one paragraph

**Thermal Captcha** is a public-facing **6-AFC cross-modal matching game**: participants feel one of 37 programmed dynamic thermal waveforms (pulse, slow-up/fast-down, fast-up/slow-down, or flat; ±1–10 °C from 32 °C; ~2 s) via a QST TCS thermode, then select the schematic time–temperature plot that best matches their sensation. Sessions are 10 trials with difficulty-controlled amplitude subsets. The system logs choices and optional verified device traces. We seek guidance on related thermo-tactile literature, the perceptual mechanisms involved, and how to evolve this demo into a controlled experiment — or whether the cross-modal matching framing is better treated as outreach only.

---

*Prepared for external scientific consultation. Hardware validation ongoing; parameters reflect the implemented codebase as of June 2026.*
