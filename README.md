# Polytes

<div align="center">

**A living, non-scripted desktop "pet"**

![Python](https://img.shields.io/badge/Python-3-3776AB?style=flat&logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-Desktop-41CD52?style=flat&logo=qt&logoColor=white)
![Status](https://img.shields.io/badge/status-in%20development-yellow?style=flat)
![License](https://img.shields.io/badge/license-GPLv3-blue?style=flat)

[**itch.io page**](https://foxcuukinho.itch.io/polytes) · [**Support on Patreon**](https://www.patreon.com/c/Polytes)

</div>

---

## Contents

- [What it is](#what-it-is)
- [Status](#status)
- [Running the project](#running-the-project)
- [Support the project](#support-the-project)
- [How it works](#how-it-works)
- [Main systems](#main-systems)
- [Technologies](#technologies)
- [Project structure](#project-structure)
- [V1 scope](#v1-scope)
- [License](#license)

---

## What it is

**Polytes** is a desktop pet: stickmen that live freely on your screen, with real physics, procedurally generated personality, and emergent, non-scripted behavior. Each stickman decides on its own whether to stand still or walk, based on personality traits and internal needs that change over time.

The goal of V1 is not just to "prove the concept". It is to already deliver the feeling of a **real physical being**, not a shimeji standing still on your screen.

You can drag the stickman by its body, let go while it's moving, and it reacts like a rag doll (ragdoll), bouncing off the screen edges.

The project is inspired by the series **Animator vs. Animation**, and built from scratch in Python.

---

## Status

> 🚧 **Under active development.** The code here changes often and there is no official release yet. This is **V1**: the brain (Utility AI) and the animation are intentionally still very simple. Don't expect a stickman at the level of *Animator vs. Animation*; the movement is procedural and still has rough edges. More behaviors and polish are on the way.

- All of V1's core systems are implemented, but **no build has been published yet** (no `.exe`, no AppImage, no `.deb`).
- A compiled build for **Windows** and **Linux** is planned for [itch.io](https://foxcuukinho.itch.io/polytes), so you won't need to install Python or dependencies manually. The page exists, but has no downloads yet.
- Until then, running from source with `python main.py` is the only way to use it. This repository is the project's source code.

> ⚠️ **Build warning (September 2026):** the commits from September 6 are broken for building. The compiled Windows version crashes when creating a stickman. Some planned polish also missed that batch of commits.

---

## Running the project

### Prerequisites

- Python 3.x
- PyQt5
- `python-xlib` (Linux, only needed for always-on-top via X11)

```bash
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

This opens the **Stickman creator** window: pick a name, a color, and whether the head is hollow or filled, click **Create Stickman**, and it appears on your screen.

### Interacting

- **Click and drag** any part of the stickman's body to handle it like a rag doll
- **Let go while moving** to see the throw with inertia
- The stickman bounces off the screen edges and reacts to collisions with real windows while "flying" (`flying`)
- Once released, it goes back to walking/standing still on its own, according to its personality
- To delete a stickman, end its corresponding process in your system's task manager

---

## Support the project

Want to support Polytes or share your ideas? Check out the project's Patreon: **[patreon.com/c/Polytes](https://www.patreon.com/c/Polytes)**

---

## How it works

```
Stickman creator (name, color, hollow/filled head)
              ↓
Name → deterministic seed (SHA-256) → personality traits
              ↓
   energy (0-100)         curiosity (0-100)
              ↓
        StickmanNeeds (stamina, boredom change over time)
              ↓
        StickmanBrain (Utility AI decides IDLE or WALK)
              ↓
   StickmanPhysics (gravity, collision, movement, ragdoll)
              ↓
   StickmanAnimator (procedural animation, IK/FK, interpolation)
              ↓
        draw_stickman (drawing on the transparent overlay window)
```

Each stickman is drawn in a transparent, borderless `PyQt5` window covering the whole screen, with a mask (`QRegion`) recalculated every frame. Only the stickman's "silhouette" is clickable/visible; the rest of the window is invisible.

On Linux, the window also receives EWMH hints via X11 (`_NET_WM_STATE_ABOVE`, `SKIP_TASKBAR`, `SKIP_PAGER`, and window type `DOCK`), keeping the stickman always visible on top of other windows, hidden from Alt-Tab/taskbar, and surviving "show desktop" (Win+D / Super+D). Tested on GNOME and KDE.

---

## Main systems

| System | Description |
|---|---|
| **Procedural personality** | The name becomes a seed via `hashlib.sha256`; an isolated `random.Random(seed)` generates `energy`/`curiosity`; hollow head and color (hue) apply buffs to the traits |
| **Dynamic needs** | `stamina` and `boredom` go up/down every frame depending on the current state, modulated by `curiosity`/`energy` |
| **Utility AI** | `StickmanBrain` sums the "utilities" of 4 factors to decide between `IDLE` and `WALK`, with cooldown/hysteresis to avoid switching state every frame |
| **Procedural animation (FK)** | Generic joint system via `RIG` (`rig.py`), with linear interpolation between frames to avoid "choppy" animation |
| **Physical ragdoll (Verlet/Jakobsen)** | When dragged and released, the body becomes physical points (`RagPoint`) connected by distance constraints (`solve_bone`): real inertia, throwing, and bouncing off the screen edges |
| **System window collision** | Via `pywinctl`: the stickman lands on top of real windows, reacts to side/top/bottom collisions, and walks off them back to the real ground |
| **Fullscreen overlay + mask** | The window covers the whole screen from the start (never resized), only the mask (`setMask`) changes per frame, avoiding Qt compositing artifacts |
| **Always-on-top via X11** | EWMH hints (`ABOVE`, `SKIP_TASKBAR`, `SKIP_PAGER`, window type `DOCK`) keep the stickman always visible, hidden from Alt-Tab, and surviving "show desktop" |
| **Ghost process** | Each stickman has its own operating system process (named, visible in the task manager); killing that process actually deletes the stickman |

---

## Technologies

| Layer | Technology |
|---|---|
| Language | Python 3 |
| UI / Window | PyQt5 (`QWidget`, `QPainter`, `QTimer`, `QRegion`) |
| Physics | Verlet integration / Jakobsen constraints, custom implementation |
| System window collision | `pywinctl` |
| Always-on-top (Linux) | `python-xlib` (EWMH hints) |
| IDE | VS Code + Pylance |

---

## Project structure

```
Polytes/
├── main.py                      # Entry point
│
├── Animation/
│   ├── animations.py            # IDLE / WALK frames
│   ├── stickman_animator.py     # Interpolation and animation cycle
│   ├── rig.py                   # Joint definitions (RIG)
│   ├── rig_editor.py            # Rig/pose editor
│   └── draw_stickman.py         # Drawing the stickman on screen
│
├── Assets/                      # Fonts and other resources
│
├── Body/
│   └── body_physics.py          # FK (calculate_joints) + Ragdoll (RagPoint, solve_bone, solve_body)
│
├── Brain/
│   ├── stickman_personality.py  # Procedural personality generation
│   ├── stickman_needs.py        # Stamina / boredom
│   └── stickman_brain.py        # Utility AI (state decision)
│
├── CreatorWindow/
│   ├── creator_window.py        # Creation window (name, color, head)
│   ├── color_picker.py          # Custom HSV color picker dialog
│   ├── preview_widget.py        # Stickman preview in the editor
│   └── widgets.py               # Custom widgets (e.g. ToggleSwitch)
│
├── Simulation/
│   ├── simulation.py            # Main QTimer, update loop
│   ├── stickman.py              # Stickman class (data)
│   ├── stickman_manager.py      # Coordinates all active stickmen
│   ├── stickman_ghost_process.py # Process tied to the stickman
│   ├── stickman_overlay.py      # Transparent window + mouse events
│   ├── stickman_physics.py      # Gravity, collision, movement
│   └── stickman_ragdoll.py      # Ragdoll logic and window collision
│
└── Utils/
    ├── constants.py              # Global project constants
    ├── helpers.py                # Geometry, collisions, hash, seed, polar_point
    └── x11_hints.py              # EWMH hints (always-on-top, dock, skip taskbar/pager)
```

---

## V1 scope

**In scope:**
- World physics (gravity, ground, screen edges, system window collision)
- Procedural personality from the name
- Dynamic needs (stamina, boredom) influencing decisions
- Simple Utility AI (IDLE / WALK)
- Real horizontal movement toward a chosen target
- Procedural drawing via the joint system (RIG)
- Animation with interpolation between frames
- Minimal creation editor (name, color, hollow/filled head)
- Full physical ragdoll: dragging, throwing with inertia, bouncing off edges and windows
- Real always-on-top via X11 (Linux)
- Ghost process (delete a stickman via the task manager)

**Out of V1 scope** (planned or considered for V1.x/V2):
- Collision between multiple stickmen
- Body self-collision
- Actively climbing system windows
- Hierarchical goal AI (`GO_TO_WINDOW`, sub-goals)
- Disk persistence, long-term personality drift
- Squash/stretch and more refined animations
- Custom color picker (Hue/Saturation bars): V1 uses its own color picker, see `color_picker.py`
- Own file format (`.stickfigure`), sharing hub, multiple walk presets
- Always-on-top on Wayland (known limitation, EWMH hints don't apply outside X11)

---

## License

Polytes' code is licensed under **GPL v3**. This means any modified version that is distributed (even commercially) must keep its source code open under the same license, and keep the original authorship credits.

> **About the name:** "Polytes" is the name/brand of this specific project. Forks and modified versions are welcome under the terms of the GPL v3, but they can't present themselves as the official "Polytes" or use the name as if they were the original version. Please use a different name for your fork.
