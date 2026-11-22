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
- `sim/scenes/`: one `.usda` per task that lays out its static fixtures (a floor tile the size of `env_spacing`, tables, shelves, targets) from `sim/assets/`. Robots, articulated props, sensors, and the shared light stay in the task's Python config.
- Assets are USD. Visual meshes are exported from Blender (keep the `.blend` under `source/`); physics (rigid bodies, colliders, joints) lives in a small `.usda` that references those visuals, because Blender's USD export carries no physics. Author URDF/MJCF only when a tool outside Isaac needs the asset.
- Versions are pinned for the team: Isaac Lab v3.0.0 as the `third_party/IsaacLab` submodule, and Isaac Sim 6.2.0 plus torch in `environment.yml`. Change them only together, in one commit, matching the `[tool.isaaclab.versions]` table in the submodule's `pyproject.toml`, and rerun the smoke test.
- Isaac Lab 3.0 differs from older docs: task IDs have no `-v0` suffix, quaternions are (x, y, z, w), and scripts have no `--headless`/`--enable_cameras` flags (headless is the default; pass `enable_cameras=True` to `AppLauncher`).
- `docs/proposal/`: project proposal and design source of truth.
- `docs/course/`: course-provided materials (private).
- `docs/papers/`: reference papers (PDF plus Markdown conversion).
- `docs/images/`: figures referenced by Markdown docs, one folder per source document.
- `docs/ai/`: AI-generated plans, analyses, and working notes.
- `docs/artifacts/`: human-readable deliverables and visualizations (e.g., HTML).

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **cs50700-robot-learning** (227 symbols, 275 relationships, 0 execution flows).

> Index stale? Run `node .gitnexus/run.cjs analyze --index-only` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? Bootstrap with `npx`, `bunx`, or `pnpm dlx` — e.g. `bunx gitnexus@latest analyze` (npm 11 npx crash; #1939).

## Always Do

- **MUST run impact before editing.** Use `impact({target: "symbolName", direction: "upstream"})` or `node .gitnexus/run.cjs impact "symbolName" --direction upstream --repo .`; report callers, processes, and risk. Never substitute grep for graph analysis.
- **MUST analyze graph changes before committing.** Use `detect_changes({scope: "all"})` (MCP) or `node .gitnexus/run.cjs detect-changes --scope all --repo .` (CLI fallback). `partial: true` or `truncated: true` is not a clean check — a zero means unseen, not unaffected; re-run it. For regression review: `detect_changes({scope: "compare", base_ref: "main"})` or `node .gitnexus/run.cjs detect-changes --scope compare --base-ref "main" --repo .`.
- MUST warn on HIGH/CRITICAL `risk` pre-edit; never use `riskSharedAxes` to waive a HIGH/CRITICAL `risk` warning. Compare File/symbol: MCP File omits axes; Graph-RAG expands File.
- **MUST treat `risk: UNKNOWN` as unresolved, not as low.** An empty caller set is not evidence the symbol is unused — it can also mean the callers are not resolvable by the index (plain-object property access, dynamic dispatch, cross-language calls). `impact` pairs `UNKNOWN` with a `riskNote` saying so. Confirm with a text search before treating the symbol as safe to change or delete; do not proceed on the strength of a zero.
- **MUST use `query({search_query: "concept"})` for concepts/flows, `context({name: "symbolName"})` for a named symbol, or `impact` for blast radius, on read-only callers, dependencies, imports, or execution flow.** Graph first; text search only for empty/`UNKNOWN`/literals.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method before MCP/CLI impact analysis.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis, and never read `UNKNOWN` as an all-clear — it means the walk could not answer, which is the one verdict that requires confirming by other means.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit before MCP/CLI graph change analysis.

## Resources

| Resource | Use for |
| --- | --- |
| `gitnexus://repo/cs50700-robot-learning/context` | Codebase overview, check index freshness |
| `gitnexus://repo/cs50700-robot-learning/clusters` | All functional areas |
| `gitnexus://repo/cs50700-robot-learning/processes` | All execution flows |
| `gitnexus://repo/cs50700-robot-learning/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
| --- | --- |
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
