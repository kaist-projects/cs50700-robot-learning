# Sequential Action Generation for Bimanual Manipulation

KAIST CS577 (Fall 2026), Team 8. The left Franka holds a camera, and the right presses its shutter. We fine-tune π0.5 for cumulative action generation (hand position → orientation → gripper motion).

## Layout

The work proceeds in stages, and each stage gets its own folder when we reach it.

```
📁 robot-learning/
├── 📁 sim/                  # 1. Simulation (conda isaacsim: Isaac Sim 6.2, Isaac Lab 3.0)
│   ├── 📁 assets/           #    every USD the env loads
│   ├── 📁 bimanual_sim/     #    task definition: scene, actions, observations
│   └── 📁 scripts/          #    📄 smoke_test.py
├── 📁 collect/   (next)     # 2. Demo collection, HDF5 → LeRobot (conda isaacsim)
├── 📁 train/     (later)    # 3. π0.5 fine-tuning (OpenPi's own environment)
├── 📁 docs/                 # proposal, papers, notes
└── 📄 README.md
```

## Simulation environment

Task `Bimanual-CameraShutter-Franka`. Two fixed-base Franka Panda arms with parallel grippers face each other across a table. The left arm (+y) holds the camera, the right arm (-y) presses the shutter, and the green post is the subject to aim at.

| | |
| --- | --- |
| Action (16D, in this order) | left hand pose 7, left gripper 1, right hand pose 7, right gripper 1 |
| Hand pose | `panda_hand` position (m) + quaternion (x, y, z, w) in that arm's base frame, solved by IK |
| Gripper | negative closes, zero or positive opens |
| Observations | joint positions, hand and camera poses (world frame), shutter joint position, lens aim error (angle between the lens axis and the subject), four 224×224 RGB cameras (table, left wrist, right wrist, and the camera prop's own lens) |
| Shutter button | prismatic joint with a return spring: 0 released, -4 mm fully pressed |
| Success | the shutter is pressed past -3 mm (the photo is taken); the episode ends there |
| Control rate | 20 Hz (physics 100 Hz) |

Run the smoke test from the repository root:

```bash
conda activate isaacsim
PYTHONPATH=sim python sim/scripts/smoke_test.py                        # headless
PYTHONPATH=sim python sim/scripts/smoke_test.py --viz kit --keep_open  # GUI window
```

It holds both hands, presses the shutter with the right hand, prints the lens aim error, the shutter travel and the success check, and saves camera frames to `sim/outputs/smoke/`. With `--keep_open` the app keeps running until you close the window. The GUI needs a desktop session, such as RDP into the workstation.

## Assets

All assets live in `sim/assets/`, so the environment needs no asset server.

- `franka_panda/`: Isaac Lab's Franka Panda (`Isaac/IsaacLab/Robots/FrankaEmika/Legacy/` from NVIDIA's Isaac 6.1 asset server).
- `camera_prop/`: a rangefinder camera with a spring-loaded shutter button. `camera.usda` holds the physics (links, joint, colliders). The visuals in `visuals/` come from Poly Haven [Camera 01](https://polyhaven.com/a/Camera_01) (CC0), split in Blender (`source/camera_01_split.blend`).
