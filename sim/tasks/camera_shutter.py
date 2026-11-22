"""Camera-shutter task: the left Franka picks up a camera and aims it at a green post; the right presses the shutter.

The file reads top to bottom as the parts of the task:
- Settings: the values to adjust while experimenting or collecting data.
- CameraShutterSceneCfg: what exists in the world.
- ObservationsCfg: what is read from the world each step, which a policy sees and a demo records.
- EventsCfg and TerminationsCfg: how an episode resets and when it ends.
- CameraShutterEnvCfg: the whole task, with the 16D bimanual action from common/franka.py.

Positions are in the env frame: +x points from the arms toward the subject, +y to the left, z = 0 is the table top.
"""

import math
from dataclasses import dataclass
from pathlib import Path

from isaaclab_physx.physics import PhysxCfg

import isaaclab.envs.mdp as mdp
import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import CameraCfg
from isaaclab.utils import configclass

from isaaclab_tasks.utils.presets import set_isaac_rtx_global_settings

from common import camera, frames, franka

SIM_DIR = Path(__file__).resolve().parents[1]
CAMERA_PROP_USD = SIM_DIR / "assets" / "camera_prop" / "camera.usda"
SCENE_USD = SIM_DIR / "scenes" / "camera_shutter.usda"


# Settings: adjust these while experimenting or collecting data. The subject itself is placed in SCENE_USD.


@dataclass(frozen=True)
class TimingSettings:
    """How fast physics and control run, and how long a policy has to finish.

    Control runs at 20 Hz to match OpenPi's Franka pre-training data. Demo recording and Mimic ignore episode length.
    """

    physics_dt_s: float = 0.01
    physics_steps_per_action: int = 5
    episode_length_s: float = 30.0


@dataclass(frozen=True)
class OutcomeSettings:
    """When an episode succeeds (the shutter is pressed this deep) or fails (the camera drops this far)."""

    shutter_press_depth_m: float = 0.003
    camera_drop_m: float = 0.1


@dataclass(frozen=True)
class LayoutSettings:
    """Where the two arms stand (left at +y, right at -y) and where the camera prop starts on the table."""

    arm_base_y_m: float = 0.5
    camera_prop_start: tuple[float, float, float] = (0.35, 0.15, 0.001)


@dataclass(frozen=True)
class ImageSettings:
    """What the four RGB cameras record. 224 px is OpenPi's input size, so frames need no resizing."""

    image_size: int = 224
    light_intensity: float = 2000.0
    table_cam_eye: tuple[float, float, float] = (-0.3, 0.0, 1.5)
    table_cam_target: tuple[float, float, float] = (0.4, 0.0, 0.05)
    table_cam_focal_length_mm: float = 18.0


TIMING = TimingSettings()
OUTCOME = OutcomeSettings()
LAYOUT = LayoutSettings()
IMAGES = ImageSettings()


def _rgb_obs(camera_name: str) -> ObsTerm:
    return ObsTerm(func=mdp.image_rgb, params={"sensor_cfg": SceneEntityCfg(camera_name), "normalize": False})


def _look_at(eye: tuple[float, float, float], target: tuple[float, float, float]) -> CameraCfg.OffsetCfg:
    """Camera offset at `eye` looking at `target`, both in the env frame."""
    return CameraCfg.OffsetCfg(pos=eye, rot=frames.look_at_quat(eye, target), convention="world")


@configclass
class CameraShutterSceneCfg(InteractiveSceneCfg):
    """What exists in the world.

    The light, the static fixtures from SCENE_USD (floor, table, rack, green post), two Franka arms, the camera
    prop with its spring-loaded shutter, and four RGB cameras. Each attribute name is how code refers to that
    object, as in env.scene["lens_cam"].
    """

    light = AssetBaseCfg(
        prim_path="/World/Light",
        spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=IMAGES.light_intensity),
    )
    fixtures = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Scene", spawn=sim_utils.UsdFileCfg(usd_path=str(SCENE_USD)))

    robot_left = franka.arm_cfg("RobotLeft", pos=(0.0, LAYOUT.arm_base_y_m, 0.0), yaw_deg=-90.0)
    robot_right = franka.arm_cfg("RobotRight", pos=(0.0, -LAYOUT.arm_base_y_m, 0.0), yaw_deg=90.0)

    camera_prop = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/CameraProp",
        spawn=sim_utils.UsdFileCfg(usd_path=str(CAMERA_PROP_USD)),
        init_state=ArticulationCfg.InitialStateCfg(pos=LAYOUT.camera_prop_start, joint_pos={"shutter_joint": 0.0}),
        actuators={
            "shutter_spring": ImplicitActuatorCfg(joint_names_expr=["shutter_joint"], stiffness=500.0, damping=5.0)
        },
    )

    table_cam = CameraCfg(
        prim_path="{ENV_REGEX_NS}/TableCam",
        height=IMAGES.image_size,
        width=IMAGES.image_size,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=IMAGES.table_cam_focal_length_mm, horizontal_aperture=20.955, clipping_range=(0.05, 5.0)
        ),
        offset=_look_at(eye=IMAGES.table_cam_eye, target=IMAGES.table_cam_target),
    )
    left_wrist_cam = franka.wrist_cam_cfg("RobotLeft", image_size=IMAGES.image_size)
    right_wrist_cam = franka.wrist_cam_cfg("RobotRight", image_size=IMAGES.image_size)
    lens_cam = CameraCfg(
        prim_path="{ENV_REGEX_NS}/CameraProp/body/lens_cam",
        height=IMAGES.image_size,
        width=IMAGES.image_size,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(focal_length=50.0, horizontal_aperture=36.0, clipping_range=(0.01, 5.0)),
        offset=CameraCfg.OffsetCfg(pos=(0.071, 0.0099, 0.0338), rot=(0.0, 0.0, 0.0, 1.0), convention="world"),
    )


@configclass
class ObservationsCfg:
    """What is read from the world each step.

    The policy group is what a policy sees and what a recorded demo stores. Each term applies a function to a
    scene object named with SceneEntityCfg. Images and vectors stay as separate terms.
    """

    @configclass
    class PolicyCfg(ObsGroup):

        left_joint_pos = ObsTerm(func=mdp.joint_pos, params={"asset_cfg": SceneEntityCfg("robot_left")})
        right_joint_pos = ObsTerm(func=mdp.joint_pos, params={"asset_cfg": SceneEntityCfg("robot_right")})
        left_hand_pose = ObsTerm(
            func=mdp.body_pose_w, params={"asset_cfg": SceneEntityCfg("robot_left", body_names=["panda_hand"])}
        )
        right_hand_pose = ObsTerm(
            func=mdp.body_pose_w, params={"asset_cfg": SceneEntityCfg("robot_right", body_names=["panda_hand"])}
        )
        camera_prop_pose = ObsTerm(
            func=mdp.body_pose_w, params={"asset_cfg": SceneEntityCfg("camera_prop", body_names=["body"])}
        )
        shutter_pos = ObsTerm(func=mdp.joint_pos, params={"asset_cfg": SceneEntityCfg("camera_prop")})
        lens_aim_error = ObsTerm(
            func=camera.lens_aim_error,
            params={"sensor_cfg": SceneEntityCfg("lens_cam"), "target_prim": "Scene/Subject"},
        )
        table_cam = _rgb_obs("table_cam")
        left_wrist_cam = _rgb_obs("left_wrist_cam")
        right_wrist_cam = _rgb_obs("right_wrist_cam")
        lens_cam = _rgb_obs("lens_cam")

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = False

    policy: PolicyCfg = PolicyCfg()


@configclass
class EventsCfg:
    """What a reset does: every object returns to its initial state."""

    reset_all = EventTerm(func=mdp.reset_scene_to_default, mode="reset")


@configclass
class TerminationsCfg:
    """When an episode ends: the time budget runs out, the camera drops, or the shutter is pressed (success)."""

    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    camera_dropped = DoneTerm(
        func=mdp.root_height_below_minimum,
        params={"minimum_height": -OUTCOME.camera_drop_m, "asset_cfg": SceneEntityCfg("camera_prop")},
    )
    success = DoneTerm(
        func=mdp.joint_pos_out_of_manual_limit,
        params={
            "bounds": (-OUTCOME.shutter_press_depth_m, math.inf),
            "asset_cfg": SceneEntityCfg("camera_prop", joint_names=["shutter_joint"]),
        },
    )


@configclass
class CameraShutterEnvCfg(ManagerBasedRLEnvCfg):
    """The whole task: the parts above, the 16D bimanual action, and simulation timing and rendering.

    env_spacing matches the 5 m floor tile in SCENE_USD, so cloned envs neither overlap nor appear in each other's view.
    """

    scene: CameraShutterSceneCfg = CameraShutterSceneCfg(num_envs=1, env_spacing=5.0)
    observations: ObservationsCfg = ObservationsCfg()
    actions: franka.BimanualActionsCfg = franka.BimanualActionsCfg()
    events: EventsCfg = EventsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    rewards = None
    commands = None
    curriculum = None

    def __post_init__(self):
        self.sim.dt = TIMING.physics_dt_s
        self.decimation = TIMING.physics_steps_per_action
        self.episode_length_s = TIMING.episode_length_s
        self.sim.render_interval = self.decimation
        self.sim.physics = PhysxCfg(
            bounce_threshold_velocity=0.01,
            friction_correlation_distance=0.00625,
            solve_articulation_contact_last=True,
        )
        self.viewer.eye = (-1.2, 0.0, 1.0)
        self.viewer.lookat = (0.4, 0.0, 0.1)
        self.num_rerenders_on_reset = 3
        scene = self.scene
        for camera_cfg in (scene.table_cam, scene.left_wrist_cam, scene.right_wrist_cam, scene.lens_cam):
            set_isaac_rtx_global_settings(camera_cfg.renderer_cfg, antialiasing_mode="DLAA")
