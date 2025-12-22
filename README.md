# Tag Ratio Add-on for Anki

## Overview

**Tag Ratio** is an Anki add-on that visualizes learning coverage by calculating tag-based completion ratios across decks.
It is designed for large, structured collections where *coverage*, *progress*, and *balance* across topics matter.

The add-on:

* Computes ratios based on tags (e.g. `needs_coverage_key`, `why`, `clinical`)
* Displays results directly on the **Main screen / Deck Browser**
* Supports flexible deck scoping (single, multiple, parent + subdecks)
* Provides a **custom Config GUI** via *Tools → Add-ons → Config*

This add-on is intentionally **non-intrusive**: no extra buttons are added to the UI beyond the existing Tools menu actions.

---

## Key Features

### 1. Tag-based Ratio Calculation

* Counts cards matching specified tags
* Calculates percentages per tag
* Supports **OR / AND** logic for multiple tags

Example use cases:

* Coverage tracking (`needs_coverage_key`)
* Learning stage tracking (`why`, `definition`, `clinical`)
* QA or review completeness checks

---

### 2. Flexible Deck Scoping

Deck selection is controlled by an **Anki search query** called `search_scope`.

Supports:

* All decks
* Single deck
* Multiple decks
* Parent decks with all subdecks

Examples:

```
deck:*
```

```
deck:"My Deck"
```

```
deck:"Parent" or deck:"Parent::*"
```

#### Multi-line Mode (Recommended)

You may enter **one scope per line** in the Config GUI:

```
deck:"My Deck"
deck:"Another Deck"
deck:Parent
```

* You do **not** need to write `OR`
* Each line is normalized automatically
* All scopes are combined with `OR`

---

### 3. Automatic Normalization

Each deck scope is automatically normalized to:

```
(deck:"X" or deck:"X::*")
```

This ensures:

* Deck names with spaces always work
* Parent decks always include subdecks
* Manual mistakes are minimized

---

### 4. Custom Config GUI

Open via:

> **Tools → Add-ons → Tag Ratio → Config**

The Config GUI allows you to configure:

* UI target (Main screen / disabled)
* Deck search scope (multi-line supported)
* Tags (comma-separated)
* Tag mode (OR / AND)
* Minimum card threshold
* Maximum rows to display
* Percentage color bands (with live color picker)

No settings buttons are added to the Tools menu.

---

### 5. Visual Indicator Bands

You can define percentage bands with colors:

| Range (%) | Meaning (example) |
| --------- | ----------------- |
| 0–40      | Critical (red)    |
| 40–70     | Low (orange)      |
| 70–90     | Good (green)      |
| 90–100    | Excellent (blue)  |

These bands are rendered as colored dots next to deck names.

---

### 6. Manual Update Options

From **Tools** menu:

* **Tag Ratio: Update now**
  Forces recomputation immediately

* **Tag Ratio: Open dialog**
  Opens the detailed ratio dialog

---

### 7. Optional Auto Update (Advanced)

The add-on can be configured to auto-update after study sessions:

* Trigger: **Reviewer close (after finishing study)**
* Safe default: OFF
* Recommended for collections with ≤100k cards in scope

This avoids unnecessary background work while keeping ratios fresh.

---

## Performance Notes

Performance depends primarily on:

* Number of cards matched by `search_scope`
* Number of tags specified

Approximate behavior:

* ≤20k cards: instant
* 20k–100k cards: 1–3 seconds
* 100k+ cards: consider disabling auto-update

Deck count alone does *not* significantly affect performance.

---

## Design Philosophy

* Deterministic, transparent behavior
* No hidden background jobs
* No UI clutter
* Configurable but safe defaults

This add-on is intended for **serious, structured learning workflows**, especially those treating Anki decks as a long-term knowledge base rather than ad-hoc flashcards.

---

## Compatibility

* Anki 25.x
* Python 3.13+
* Qt6 / PyQt6

Tested primarily on Windows; expected to work on macOS and Linux.

---

## License

MIT License

---

## Author Notes

This add-on is part of a broader "study-as-code" workflow and is designed to integrate cleanly with:

* Coverage tracking systems
* Branch-based learning flows
* README / coverage index generators

If you are extending this add-on, keep normalization and determinism in mind.
