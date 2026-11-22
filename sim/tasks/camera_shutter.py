"""Bimanual camera-shutter environment: two fixed-base Franka arms and a camera with a pressable shutter.

World frame: +x points from the arms toward the subject, +y to the left, z = 0 is the table top.
The left arm (+y) holds the camera and the right arm (-y) presses the shutter button. Both arms
face the table centre. Stock Isaac Lab MDP terms are used, except the lens aim error from
common/camera.py. Robot, wrist-camera, and 16D action definitions live in common/franka.py.
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
SCENE_USD = SIM_DIR / "scenes" / "camera_shutter.usda"  # floor, table, rack, and the subject at Scene/Subject


# Settings to adjust while experimenting or collecting data. Positions are in the env frame
# (+x toward the subject, +y left, z = 0 the table top). The subject is placed in SCENE_USD.


@dataclass(frozen=True)
class TimingSettings:
    """Simulation rates and the episode time budget."""

    physics_dt_s: float = 0.01  # 100 Hz physics
    physics_steps_per_action: int = 5  # 20 Hz control, the rate of OpenPi's Franka pre-training data
    episode_length_s: float = 30.0  # time budget for policy evaluation; demo recording and Mimic ignore it


@dataclass(frozen=True)
class OutcomeSettings:
    """When an episode succeeds or fails."""

    shutter_press_depth_m: float = 0.003  # success: the shutter goes deeper than this (full travel is 4 mm)
    camera_drop_m: float = 0.1  # failure: the camera prop falls this far below the table top


@dataclass(frozen=True)
class LayoutSettings:
    """Where the arms stand and where the camera prop starts."""

    arm_base_y_m: float = 0.5  # left arm at +y, right arm at -y, both on the table's back edge
    camera_prop_start: tuple[float, float, float] = (0.35, 0.15, 0.001)  # bottom centre of the prop


@dataclass(frozen=True)
class ImageSettings:
    """What the four RGB cameras record: resolution, lighting, and the fixed table view."""

    image_size: int = 224  # OpenPi's input resolution, so frames need no resizing
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
    """Light, the SCENE_USD fixtures, two Franka arms, the camera prop, and four RGB cameras."""

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
        # Return spring of the shutter button: about 2 N at the full 4 mm press.
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
    # The photo the camera prop would take: a 50 mm lens on 36 mm film, looking along the lens (+x).
    lens_cam = CameraCfg(
        prim_path="{ENV_REGEX_NS}/CameraProp/body/lens_cam",
        height=IMAGES.image_size,
        width=IMAGES.image_size,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(focal_length=50.0, horizontal_aperture=36.0, clipping_range=(0.01, 5.0)),
        # 1 mm ahead of the lens glass, in the camera prop's body frame.
        offset=CameraCfg.OffsetCfg(pos=(0.071, 0.0099, 0.0338), rot=(0.0, 0.0, 0.0, 1.0), convention="world"),
    )


@configclass
class ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        """Robot state, camera prop state, and RGB frames, kept as separate terms."""

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
    reset_all = EventTerm(func=mdp.reset_scene_to_default, mode="reset")


@configclass
class TerminationsCfg:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    camera_dropped = DoneTerm(
        func=mdp.root_height_below_minimum,
        params={"minimum_height": -OUTCOME.camera_drop_m, "asset_cfg": SceneEntityCfg("camera_prop")},
    )
    # The photo is taken: the shutter joint leaves its bounds below -shutter_press_depth_m.
    success = DoneTerm(
        func=mdp.joint_pos_out_of_manual_limit,
        params={
            "bounds": (-OUTCOME.shutter_press_depth_m, math.inf),
            "asset_cfg": SceneEntityCfg("camera_prop", joint_names=["shutter_joint"]),
        },
    )


@configclass
class CameraShutterEnvCfg(ManagerBasedRLEnvCfg):
    # env_spacing equals the 5 m floor tile in SCENE_USD, so the floors of cloned envs tile
    # and the table camera does not see the neighbouring envs.
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
            # Let object contacts stall the position-driven grippers before they tunnel through a grasp.
            solve_articulation_contact_last=True,
        )
        self.viewer.eye = (-1.2, 0.0, 1.0)
        self.viewer.lookat = (0.4, 0.0, 0.1)
        self.num_rerenders_on_reset = 3
        scene = self.scene
        for camera_cfg in (scene.table_cam, scene.left_wrist_cam, scene.right_wrist_cam, scene.lens_cam):
            set_isaac_rtx_global_settings(camera_cfg.renderer_cfg, antialiasing_mode="DLAA")
