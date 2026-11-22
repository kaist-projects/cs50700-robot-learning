# Sequential Action Generation for Bimanual Manipulation

KAIST CS577 (Fall 2026), Team 8. Two Franka arms take a photo: the left arm holds a camera and the right arm presses its shutter. We fine-tune π0.5 so that it generates actions in three cumulative stages: hand position, then orientation, then gripper.

## Layout

The work proceeds in stages, and each stage gets its own folder when we reach it.

| Folder | Stage | Python environment |
| --- | --- | --- |
| `sim/` | Simulation assets and the Isaac Lab environment | conda `isaacsim` (Isaac Sim 6.2, Isaac Lab 3.0) |
| `collect/` (next) | Demonstration collection and conversion to LeRobot | conda `isaacsim` |
| `train/` (later) | π0.5 fine-tuning with OpenPi | OpenPi's own environment |
| `docs/` | Proposal, papers, notes | |

`sim/bimanual_sim` is the only definition of the task and its action layout. Later stages import it with `PYTHONPATH=sim` instead of copying it.

## Simulation environment

Task `Bimanual-CameraShutter-Franka`. Two fixed-base Franka Panda arms with parallel grippers face each other across a table. The left arm (+y) holds the camera, the right arm (-y) presses the shutter, and the green post is the subject to aim at.

| | |
| --- | --- |
| Action (16D, in this order) | left hand pose 7, left gripper 1, right hand pose 7, right gripper 1 |
| Hand pose | `panda_hand` position (m) + quaternion (x, y, z, w) in that arm's base frame, solved by IK |
| Gripper | negative closes, zero or positive opens |
| Observations | joint positions, hand and camera poses (world frame), shutter joint position, three 224×224 RGB cameras (table, left wrist, right wrist) |
| Shutter button | prismatic joint with a return spring: 0 released, -4 mm fully pressed |
| Control rate | 20 Hz (physics 100 Hz) |

Run the smoke test from the repository root:

```bash
conda activate isaacsim
PYTHONPATH=sim python sim/scripts/smoke_test.py
```

It holds both hands, presses the shutter with the right hand, prints the shutter travel, and saves camera frames to `sim/outputs/smoke/`.

## Assets

All assets live in `sim/assets/`, so the environment needs no asset server.

- `franka_panda/`: Isaac Lab's Franka Panda (`Isaac/IsaacLab/Robots/FrankaEmika/Legacy/` from NVIDIA's Isaac 6.1 asset server).
- `camera_prop/camera_prop.usda`: our camera, a body plus the spring-loaded shutter button.
