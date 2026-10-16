# Polytes - `Docs` branch

This branch is Polytes' **idea notebook**. Nobody writes program code here: only ideas, notes, and planning documents (such as the V2 scope).

## What is Polytes

Polytes is a stickman that lives on your computer. The computer is his home: windows, icons, and everything else are just more objects in the house that he can interact with.

The whole computer is his house: the system, apps, websites, files, everything. If it is on the screen, it is part of his world.

He does not just react to his house: he interacts with it and can change it. The goal is for him to feel like something truly alive inside the computer.

This describes where Polytes is heading, not what is built today. Whether an idea fits the vision and when it gets built are separate questions: the first is answered here, the second in the scope files.

Keep this in mind when writing ideas. A good idea makes the stickman feel more like someone living in that house.

## Most important rule: this branch NEVER gets merged

`Docs` lives separately from `main` forever. It is not a feature in progress: it is a permanent space.

That is why **when you open a Pull Request here, the `base` field must be `Docs`** (capital D, Git is case-sensitive). GitHub suggests `main` by default. If you leave the default, your idea tries to enter the project's code. Check the `base` before clicking "Create pull request".

## How to access it

```
git fetch origin
git switch Docs
```

If you want to read the ideas without leaving the branch you are working on, open `Docs` in a second folder:

```
git worktree add ../Polytes-Docs Docs
```

## Who can write

Any dev on the project. You can:

- edit `ideas.md` directly on the `Docs` branch, or
- open a PR with `base` = `Docs`, if you want someone to review it first.

## How to write an idea

Everyone writes in the same file: `ideas.md`. No structure needed, and you don't have to be sure about it. Drop the idea, even a raw one, at the end of the file.

Each idea starts with its status in brackets. A new idea enters as `[New]`:

```
- [New] Stickman sits down when petted (author: name)
```

## Triage

Devs organize the ideas. When an idea is decided, it is **not deleted**: its status changes and the text says where it went.

| Status | Meaning |
|---|---|
| `[New]` | Just arrived, nothing decided yet |
| `[Accepted]` | Will be done, but not yet |
| `[Postponed]` | Good idea, but not for now |
| `[Implemented]` | Already in the code |
| `[Rejected]` | We decided not to do it, with the reason |

When you change the status, note the destination:

```
- [Accepted -> v2-scope.md] Stickman sits down when petted
- [Postponed -> V3] Interaction with browser HTML elements
- [Implemented -> V1.1] Delete a stickman through the Task Manager
```

That way, anyone reading the file months from now knows what happened to each idea and where to find the details.

## What does not go here

- Polytes code (that goes in `main`).
- Bugs. A bug is a GitHub Issue, not an idea.