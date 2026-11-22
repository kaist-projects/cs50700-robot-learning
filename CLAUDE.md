# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

This repository is Team 8's final project for KAIST CS577 Robot Learning and Interaction (Fall 2026): "Sequential Action Generation for Bimanual Manipulation." The source of truth for the plan is the proposal deck in `docs/proposal/`. The `.pptx` version carries speaker notes that the `.pdf` lacks.

The project ports HAF-VLA (Gu et al., arXiv:2610.26584) from a humanoid to two fixed-base Franka arms with Allegro hands. HAF-VLA splits π0.5's single flow-matching action generation into three cumulative stages. The research question is whether arm, then wrist, then finger generation gives a more precise and faster trajectory than single-stage π0.5 with the same data and inference budget.

### Method

- The VLM prefix encodes images and language once, and all three stages share its KV cache.
- One shared action expert runs three times, identified by a stage embedding and a stage mask.
- Stage 1 generates both hands' positions (xyz) from noise.
- Stage 2 reads the stage 1 KV cache and regenerates position plus orientation.
- Stage 3 reads stages 1 and 2 and adds the finger joints. Only the stage 3 chunk is executed.
- Training masks the demo actions per stage, so each stage learns its own subset of dimensions.
- The action is each arm's end-effector pose plus 16 Allegro joint angles per hand.

### Task

In the bimanual camera-shot task, the holding hand grips a camera and aims it at a subject, and the pressing hand presses the shutter. The stage order matches the task: the arms fix the camera position, the wrists fix the aim, and the fingers press only after the hand has settled.

### Pipeline

1. Define the task spec (subject and camera poses).
2. Collect two-arm teleoperation demos.
3. Augment the demos with Isaac Lab Mimic and store them as a LeRobotDataset.
4. LoRA fine-tune π0.5 once per variant.
5. Evaluate in Isaac Lab Arena on randomized episodes.
6. Report a sensitivity analysis and an ablation table.

### Evaluation

- Baselines: single-stage π0.5, GR00T N1.7, and SmolVLA.
- Ablations: stage count (1, 2, or 3) and reversed stage order (fingers, then wrists, then arms).
- Metrics: success rate, time to shot, button miss, aim error in degrees, and inference latency.
- Sensitivity factors: subject position, camera start pose, and lighting.

### Schedule

The work runs in two-week passes, and each pass reruns the whole pipeline.

1. Pass 1 builds the pipeline with π0.5 on a fixed setup. It is done when the shutter gets pressed.
2. Pass 2 implements the staged method and compares it with π0.5 on random setups.
3. Pass 3 runs the ablations and the sensitivity analysis.

A real Franka pair or a G1 upper body is optional, if hardware becomes available.

Per the syllabus, final paper presentations are on Dec 8 and Dec 10, 2026. A 2-page, 2-column abstract paper is due Dec 17, 2026.

## Course rules that constrain this repo

- The syllabus forbids publishing provided class content in public, for example on GitHub or a blog. This repo has no remote. Do not add a public remote or push `docs/course/` or course assignment code anywhere public.
- The syllabus requires submitted reports to be written in English.

## Repository layout

There is no project code yet. Add build, train, and evaluation commands to this file once they exist.

- `docs/course/`: course-provided material, such as the syllabus.
- `docs/proposal/`: the team's proposal deck.
- `docs/ai/`: documents that AI agents write, such as plans, analyses, and notes. Put new AI-written docs here.
- `docs/artifacts/`: human-readable outputs, such as HTML artifacts.
- `.orca/drops/`: Orca's file drop area, which git ignores. Move files that land there into `docs/`.

## Tooling on this host

This host is aelab-121 with one RTX 3090 (24 GB). Use these existing installs before installing anything new.

- Isaac Lab v3.0.0-EA is at `~/repositories/IsaacLab` and is installed in the `isaacsim` conda env (Isaac Sim 6.2, torch 2.11+cu128). It includes `isaaclab_mimic` and `isaaclab_teleop`.
- LeRobot 0.6.2 is at `~/lerobot` and is installed in the `lerobot` conda env. It ships `pi05`, `smolvla`, and `groot` policies.
- Isaac-GR00T N1.7 is at `~/repositories/Isaac-GR00T-n17`, with the `gr00t-n17` and `gr00t-sim` conda envs.
- The `cs577` conda env (Python 3.12, robosuite 1.4.1, MuJoCo 3.3.0) and `~/repositories/cs577_RLI_2026Fall` hold the course assignments.
- Isaac Lab Arena and openpi are not on this host yet.
