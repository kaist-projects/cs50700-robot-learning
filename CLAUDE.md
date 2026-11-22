# CLAUDE.md

Project instructions for coding agents working in this repository.

## Project

KAIST CS577 (Fall 2026) Team 8 project: **Sequential Action Generation for Bimanual Manipulation**. We port HAF-VLA (Gu et al., arXiv:2610.26584) from a humanoid to two fixed-base Franka arms with Allegro hands on a bimanual camera-shutter task, splitting π0.5's single-stage flow matching into three cumulative stages (arms, then wrists, then fingers) with a shared VLM prefix and cross-stage KV cache.

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

- `docs/proposal/`: project proposal and design source of truth.
- `docs/course/`: course-provided materials (private).
- `docs/papers/`: reference papers (PDF plus Markdown conversion).
- `docs/images/`: figures referenced by Markdown docs, one folder per source document.
- `docs/ai/`: AI-generated plans, analyses, and working notes.
- `docs/artifacts/`: human-readable deliverables and visualizations (e.g., HTML).
