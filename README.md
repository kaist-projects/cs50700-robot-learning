# Sequential Action Generation for Bimanual Manipulation

KAIST CS577 (Fall 2026), Team 8. The left Franka holds a camera, and the right presses its shutter. We fine-tune π0.5 for cumulative action generation (hand position → orientation → gripper motion).

## Layout

```
📁 robot-learning/
├── 📁 sim/
│   ├── 📁 assets/
│   ├── 📁 scenes/
│   ├── 📁 tasks/
│   ├── 📁 common/
│   └── 📁 scripts/
│       └── 📄 smoke_test.py
├── 📁 collect/    # Demo collection (next)
├── 📁 train/      # π0.5 fine-tuning (later)
├── 📁 docs/
├── 📁 third_party/
│   └── 📁 IsaacLab/  # v3.0.0, git submodule
├── 📄 environment.yml
└── 📄 README.md
```

## Setup

Requires Linux with an NVIDIA RTX GPU, Isaac Sim 6.2.0 (`environment.yml`), and Isaac Lab v3.0.0 (`third_party/IsaacLab` submodule).

```bash
git clone --recursive https://github.com/kaist-projects/cs50700-robot-learning.git
cd cs50700-robot-learning
conda env create -f environment.yml
conda activate isaacsim
# Install Isaac Lab in the active Conda environment
./third_party/IsaacLab/isaaclab.sh -i
```

## Simulation environment

In `Bimanual-CameraShutter-Franka`, the left arm holds and aims the camera at a green post while the right arm presses the shutter.

| Component | Setup |
| --- | --- |
| Simulator | Isaac Sim 6.2.0 with Isaac Lab v3.0.0 |
| Robot arms | Two fixed-base Franka Panda arms |
| Grippers | Franka Panda two-finger parallel grippers |
| Camera | Poly Haven's Camera 01 rangefinder model with a spring-loaded shutter button |

![Two Franka Panda arms with parallel grippers facing each other across the work table, with the camera on it and the green post on a rack beyond it](docs/images/readme/franka-panda-workcell.png)

| Camera prop in Blender | Before pressing | Shutter pressed |
| --- | --- | --- |
| ![Camera 01 rangefinder with its shutter button visible](docs/images/readme/camera-prop.png) | ![Closed gripper hovering above the shutter button in Isaac Lab](docs/images/readme/shutter-approach.png) | ![The same gripper lowered onto the shutter button in Isaac Lab](docs/images/readme/shutter-press.png) |

### Task definition

[`sim/tasks/camera_shutter.py`](sim/tasks/camera_shutter.py) defines the task. It is a config, not a script. [`sim/tasks/__init__.py`](sim/tasks/__init__.py) registers it as `Bimanual-CameraShutter-Franka`, and every script that runs the task (demo recording, replay, Mimic, policy evaluation) builds the same environment from that ID. Other stages import it rather than copy it, so a change here changes what every stage records and sees.

| Config | Defines |
| --- | --- |
| `CameraShutterSceneCfg` | What is in the world: the light, the static scene [`sim/scenes/camera_shutter.usda`](sim/scenes/camera_shutter.usda) (floor, table, rack, green post), two Franka arms, the camera prop with its shutter spring, and four RGB cameras (table, both wrists, lens). |
| `actions` | How a 16D action moves the arms: left hand pose (7), left gripper (1), right hand pose (7), right gripper (1). A hand pose is xyz plus an xyzw quaternion in that arm's base frame, solved by IK. A negative gripper value closes it. |
| `ObservationsCfg` | What a policy sees and a demo records: joint positions, hand poses, camera pose, shutter position, lens aim error, and four 224×224 RGB images. |
| `EventsCfg` | What a reset does: every object returns to its initial pose. |
| `TerminationsCfg` | When an episode ends: a 30 s timeout, the camera dropping more than 10 cm below the table top, or success, which is the shutter pressed past 3 mm. |
| `CameraShutterEnvCfg` | Timing and physics: 100 Hz physics and 20 Hz control, so each action runs 5 physics steps. |

Run from the repository root.

```bash
conda activate isaacsim

# Open the static scene in Isaac Sim
isaacsim --exec "open_stage.py '$PWD/sim/scenes/camera_shutter.usda'"

# Run the smoke test
python sim/scripts/smoke_test.py
```

## Assets

The simulation loads its assets from [`sim/assets/`](sim/assets/).

| Folder | Asset | Source |
| --- | --- | --- |
| [`franka_panda/`](sim/assets/franka_panda/) | Franka Panda arm with a two-finger gripper | [Isaac Lab USD](https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.1/Isaac/IsaacLab/Robots/FrankaEmika/Legacy/panda_instanceable.usd) |
| [`camera_prop/`](sim/assets/camera_prop/) | Rangefinder camera with a spring-loaded shutter | [Poly Haven Camera 01 (CC0)](https://polyhaven.com/a/Camera_01) |
| [`packing_table/`](sim/assets/packing_table/) | Heavy-duty worktable | [Isaac Sim Packing Table USD](https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.1/Isaac/Props/PackingTable/props/SM_HeavyDutyPackingTable_C02_01/SM_HeavyDutyPackingTable_C02_01.usd) |
| [`office_rack/`](sim/assets/office_rack/) | Storage rack for the green target | [Isaac Sim Office Rack USD](https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.1/Isaac/Environments/Office/Props/SM_Rack1m.usd) |
