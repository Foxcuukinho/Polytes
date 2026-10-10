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
- [Technical deep dive](#technical-deep-dive)
- [Technologies](#technologies)
- [Project structure](#project-structure)
- [V1 scope](#v1-scope)
- [License](#license)

---

## What it is

**Polytes** is a program that puts stickmen to life on your computer. They aren't images or GIFs: each one is drawn and animated procedurally, and runs on real ragdoll physics. Grab any part of its body, let go, and watch it fall and react with real inertia, bouncing off the screen edges and colliding with the windows you have open.

Each stickman also has its own **personality**, generated from the name you give it (plus its color and head type). Personality changes how it behaves: some walk around more, others rest more. Nothing is scripted. Every stickman decides on its own what to do, based on internal needs (like stamina and boredom) that change over time.

**In short, you can:**
- Create a stickman by choosing a name, a color, and a hollow or filled head
- Watch it walk and stand still on its own, on your real desktop
- Grab it, throw it, and see it land on top of your windows
- Delete it by ending its process in your system's task manager

The goal of V1 is not just to "prove the concept". It is to already deliver the feeling of a **real physical being**, not a shimeji standing still on your screen. The project is inspired by the series **Animator vs. Animation**, and built from scratch in Python.

> **Heads up:** Polytes is still very simple. Right now the stickmen can only walk, stand still, and react to physics when you grab them. More behaviors are coming in future updates.

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

In simple terms, each stickman goes through these steps:

1. **Personality:** the name you type is turned into a number (a "seed"), which generates two traits: `energy` and `curiosity`. The same name always gives the same personality. Color and head type add small bonuses.
2. **Needs:** while it lives, its `stamina` and `boredom` change over time. Walking tires it out and relieves boredom, standing still rests it and makes it bored.
3. **Decision:** every few seconds, its brain compares its traits and needs and decides: walk somewhere, or stand still.
4. **Body and animation:** the body is a set of joints with angles. Animations are a list of poses, and the movement between poses is smoothed out frame by frame.
5. **Physics:** gravity pulls it down, the ground and your open windows hold it up, and when you grab it, its body turns into a ragdoll.
6. **Drawing:** everything is drawn in a transparent window over your screen, so the stickman looks like it lives right on your desktop.

Here is the same flow in more technical detail:

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

## Technical deep dive

For those who want to know exactly how it works. Values come from `Utils/constants.py` and may change as the project is tuned.

### Main loop

A single `QTimer` (`Simulation`) ticks every `FRAME_DURATION_MS = 32` ms (about 31 updates per second), with `DELTA_TIME = 0.032` s. On every tick, for each stickman, `StickmanManager` runs in this order: **brain, physics, animation, overlay**. The order matters: the brain must run before physics, otherwise on the frame where a stickman switches from `IDLE` to `WALK`, physics still sees the old state and `velocity_x` is `0`, which would cause a division by zero in the animator.

### Personality

```
seed      = int(sha256(name), 16)
rng       = random.Random(seed)            # isolated RNG, never the global one
energy    = rng.randint(0, 100)
curiosity = rng.randint(0, 100)

hollow head          → energy    *= 1.2
hue in [120, 240]    → curiosity *= 1.2    (cool colors)
any other hue        → energy    *= 1.2    (warm colors)

both traits are clamped to [1, 100] and rounded
```

The same name, color and head type always produce the same stickman.

### Needs

Updated every frame (`dt = DELTA_TIME`):

```
stamina_drain  = (65 / energy)    * dt
stamina_gain   = (energy / 50)    * dt
boredom_drain  = (curiosity / 50) * dt
boredom_gain   = (curiosity / 30) * dt

IDLE      → stamina += stamina_gain,  boredom += boredom_gain
otherwise → stamina -= stamina_drain, boredom -= boredom_drain
```

Both values are clamped to `[0, 100]`. This means a low-`energy` stickman gets tired much faster, and a high-`curiosity` one gets bored and recovers from boredom faster.

### Decision (Utility AI)

The brain only decides every `STICKMAN_DEFAULT_DECIDE_COOLDOWN = 3` seconds (a temporal hysteresis, so it doesn't flip state every frame). Each option's score is the sum of four factors scaled to `0..1`:

```
score_walk = Σ (factor / 100)         for factor in [energy, curiosity, stamina, boredom]
score_idle = Σ (1 - factor / 100)     for the same factors

WALK  if score_walk > score_idle + SCORE_MARGIN (0.3)   and the stickman is not being dragged
IDLE  if score_idle > score_walk
```

When it switches to `WALK`, it picks a random `target_x` at least 200 px away from its current position, and picks a new one when it gets within 10 px of it.

### Movement and ground

Walking moves `x` at `DEFAULT_WALK_SPEED = 170` px/s toward `target_x`. Gravity is a simple integration (`GRAVITY_ACCELERATION = 1098` px/s²): `velocity_y += g * dt`, then `y += velocity_y * dt`. The ground is the **lowest candidate** among the real screen bottom and the visible top edges of system windows that overlap the stickman horizontally and sit below its feet (with `GROUND_SNAP_TOLERANCE` to avoid losing a window by a few pixels). When the body leaves the ground area completely, the stickman switches to the physical ragdoll state (`flying`).

### Skeleton and animation

The body is a list of joints (`RIG`), each with a `parent`, a `length`, an `angle` key and a `relative` flag (relative angles add to the parent's angle). Joint positions come from **forward kinematics**:

```
position = parent_position + length * (cos(angle), sin(angle))
```

After computing all joints, the whole body is shifted vertically so the lowest foot touches the ground, whatever the pose. Limbs are drawn as quadratic curves (`QPainterPath.quadTo`) with a control point derived from the middle joint.

Animations are lists of poses (dictionaries of angles). Between two poses, each angle is **linearly interpolated**: `angle = a + (b - a) * progress`, where `progress = timer / seconds_per_frame`. For `WALK`, the cycle duration is tied to the real speed to avoid foot sliding:

```
cycle_duration = DISTANCE_PER_WALK_CYCLE (67) / velocity_x
```

### Ragdoll (Verlet / Jakobsen)

When you grab the stickman, each joint becomes a `RagPoint` that stores its **current and previous position** (velocity is implicit). Each frame:

```
x_new = x + (x - old_x) * RAGDOLL_DAMPING (0.85)
y_new = y + (y - old_y) * RAGDOLL_DAMPING + g * dt
```

Then the skeleton is held together by **distance constraints**: for every bone in the `RIG`, `solve_bone` moves the two points along their line until their distance equals the bone length. This is repeated **20 times per frame** (fewer iterations make the body stretch). While held, the grabbed point is pinned to the mouse; on release, the mouse movement is injected as velocity by setting `old = position - mouse_delta`, which is what makes throwing work.

Collisions use the ragdoll's bounding box. Screen edges and window sides push the whole body back and reflect its implicit velocity (`RAGDOLL_BOUNCE_FACTOR = 0.7`). Landing happens when the lowest point reaches a valid ground, which switches the stickman back to normal (FK) mode. Windows that already overlap the body when you release it are ignored until they stop overlapping, so you can drop a stickman inside a window without it being teleported.

### System windows

Window geometry comes from `pywinctl`. Reading properties from live window objects is slow (each read queries the system), so windows are copied into lightweight snapshots and **refreshed only every `WINDOW_UPDATE_INTERVAL_FRAMES = 60` frames**. On Linux/X11, the stacking order (`_NET_CLIENT_LIST_STACKING`) is used to compute which parts of a window's top edge are actually visible, so a stickman only stands on the exposed part of a partly covered window.

### Overlay and mouse hit-testing

Each stickman lives in a borderless, transparent, always-on-top window covering the whole screen, created once and never resized (resizing every frame caused a flicker in Qt). Only `setMask` changes per frame: the mask is built from small `QRegion` squares placed along every bone (5 per bone, radius 15 px) plus a larger one around the head, so the rest of the screen stays click-through. When the stickman faces right, the drawing is mirrored horizontally around its own position, and the mask uses the same mirroring.

### Ghost process

Each stickman has a tiny separate OS process whose only job is to rename itself (`setproctitle`) to the stickman's name and sleep. The manager polls it every frame, and when it is no longer running, the stickman is deleted. This is what makes "End task" in the task manager delete a stickman for real.

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
