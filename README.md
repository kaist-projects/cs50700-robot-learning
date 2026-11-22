# Sequential Action Generation for Bimanual Manipulation

KAIST CS577 (Fall 2026), Team 8. The left Franka holds a camera, and the right presses its shutter. We fine-tune π0.5 for cumulative action generation (hand position → orientation → gripper motion).

## Layout

```
📁 robot-learning/
├── 📁 sim/        # Isaac Sim 6.2, Isaac Lab 3.0
│   ├── 📁 assets/
│   ├── 📁 tasks/
│   ├── 📁 common/
│   └── 📁 scripts/
│       └── 📄 smoke_test.py
├── 📁 collect/    # Demo collection (next)
├── 📁 train/      # π0.5 fine-tuning (later)
├── 📁 docs/
└── 📄 README.md
```

## Simulation environment

In `Bimanual-CameraShutter-Franka`, the left arm holds and aims the camera at a green post while the right arm presses the shutter.

| Component | Setup |
| --- | --- |
| Robot arms | Two fixed-base Franka Panda arms |
| Grippers | Franka Panda two-finger parallel grippers |
| Camera | Poly Haven's Camera 01 rangefinder model with a spring-loaded shutter button |
| Table | A fixed worktable with the arms mounted opposite each other |
| RGB views | Table overview, one view from each wrist, and the camera's lens view |

See the action and observation layouts in the [task configuration](sim/tasks/camera_shutter.py).

Run the smoke test from the repository root:

```bash
conda activate isaacsim
PYTHONPATH=sim python sim/scripts/smoke_test.py                        # headless
PYTHONPATH=sim python sim/scripts/smoke_test.py --viz kit --keep_open  # GUI window
```

The smoke test presses the shutter, reports aim error, shutter travel, and task success, and saves RGB frames to `sim/outputs/smoke/`. The GUI command requires a desktop session and keeps the window open until you close it.

## Assets

All assets live in `sim/assets/`, so the environment needs no asset server.

- `franka_panda/`: Isaac Lab's Franka Panda (`Isaac/IsaacLab/Robots/FrankaEmika/Legacy/` from NVIDIA's Isaac 6.1 asset server).
- `camera_prop/`: a rangefinder camera with a spring-loaded shutter button. `camera.usda` holds the physics (links, joint, colliders). The visuals in `visuals/` come from Poly Haven [Camera 01](https://polyhaven.com/a/Camera_01) (CC0), split in Blender (`source/camera_01_split.blend`).
