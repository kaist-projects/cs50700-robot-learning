# CLAUDE.md

Project instructions for coding agents working in this repository.

## Project

KAIST CS577 (Fall 2026) Team 8 project: **Sequential Action Generation for Bimanual Manipulation**. We port HAF-VLA (Gu et al., arXiv:2610.26584) from a humanoid to two fixed-base Franka arms on a bimanual camera-shutter task, splitting π0.5's single-stage flow matching into three cumulative stages (hand position, then orientation, then gripper) with a shared VLM prefix and cross-stage KV cache.

- The arms use 1-DoF parallel grippers, not the Allegro hands in the proposal. OpenPi's π0.5 checkpoint has `action_dim=32`, and two Franka arms with Allegro hands need 46. A three-finger hand is the planned next step, so keep the total action at 32 or fewer.
- The stage split needs end-effector actions (position and orientation are separable there, not in joint space). Training actions are planned as `[L xyz, L rot6d, L grip, R xyz, R rot6d, R grip]` = 20D, converted from the env's 16D pose actions.

## Reference docs

- `docs/proposal/team8-proposal.md`: read before working on method design, task spec, data/training/eval pipeline, baselines, metrics, ablations, or schedule.
- `docs/course/cs577-syllabus-fall2026.md`: read when checking course requirements, deliverables, or deadlines.

## Rules

- Keep this repository private. Never push `docs/course/` or course assignment code to any public remote or site.
- Write all submitted reports and papers in English.
- Keep `CLAUDE.md` machine-independent. Put host-specific paths or local environment notes in an untracked `CLAUDE.local.md`.

## Commits

- Commit after every completed task. Do not bundle several tasks into one commit.
- Start each commit subject with one of these prefixes: `feat:`, `refactor:`, `fix:`, `chore:`, `docs:`.

## Directory conventions

- One top-level folder per pipeline stage, created when the stage starts: `sim/` (assets and Isaac Lab env), then `collect/`, `train/`, `eval/`. Do not number the folder names.
- `sim/tasks` holds one Python file per task (scene, observations, action layout), and `sim/tasks/__init__.py` registers them. Code shared by several tasks goes in `sim/common`. Other stages import both with `PYTHONPATH=sim`; never copy env config into another stage.
- `sim/assets/`: every asset the env loads, committed. The env must not depend on an asset server.
- Assets are USD. Visual meshes are exported from Blender (keep the `.blend` under `source/`); physics (rigid bodies, colliders, joints) lives in a small `.usda` that references those visuals, because Blender's USD export carries no physics. Author URDF/MJCF only when a tool outside Isaac needs the asset.
- Isaac Lab 3.0 differs from older docs: task IDs have no `-v0` suffix, quaternions are (x, y, z, w), and scripts have no `--headless`/`--enable_cameras` flags (headless is the default; pass `enable_cameras=True` to `AppLauncher`).
- `docs/proposal/`: project proposal and design source of truth.
- `docs/course/`: course-provided materials (private).
- `docs/papers/`: reference papers (PDF plus Markdown conversion).
- `docs/images/`: figures referenced by Markdown docs, one folder per source document.
- `docs/ai/`: AI-generated plans, analyses, and working notes.
- `docs/artifacts/`: human-readable deliverables and visualizations (e.g., HTML).
