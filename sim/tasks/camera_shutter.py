"""Bimanual camera-shutter environment: two fixed-base Franka arms and a camera with a pressable shutter.

World frame: +x points from the arms toward the subject, +y to the left, z = 0 is the table top.
The left arm (+y) holds the camera and the right arm (-y) presses the shutter button. Both arms
face the table centre. Stock Isaac Lab MDP terms are used, except the lens aim error from
common/camera.py. Robot, wrist-camera, and 16D action definitions live in common/franka.py.
"""

import math
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

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
CAMERA_PROP_USD = ASSET_DIR / "camera_prop" / "camera.usda"
SCENE_USD = Path(__file__).resolve().parents[1] / "scenes" / "camera_shutter.usda"  # floor, table, rack, subject

# Episode and simulation settings.
EPISODE_LENGTH_S = 30.0
CAMERA_DROP_HEIGHT_M = -0.1  # Relative to the table top.
SHUTTER_PRESSED_POS = -0.003  # Shutter joint position that counts as a press; fully pressed is -0.004 m.
# 100 Hz physics, 20 Hz control to match OpenPi's Franka pre-training data.
PHYSICS_DT_S = 0.01
PHYSICS_STEPS_PER_ACTION = 5
NUM_ENVS = 1

# Scene and camera settings.
ARM_BASE_Y = 0.5
CAMERA_PROP_START = (0.35, 0.15, 0.001)  # prop origin is its bottom centre
LENS_FRONT = (0.071, 0.0099, 0.0338)  # 1 mm ahead of the lens glass, in the camera prop's body frame
SUBJECT_POS = (1.1, 0.0, 0.106)  # centre of the green post on the rack; must match Subject in SCENE_USD
LIGHT_INTENSITY = 2000.0
TABLE_CAM_EYE = (-0.3, 0.0, 1.5)
TABLE_CAM_TARGET = (0.4, 0.0, 0.05)
TABLE_CAM_FOCAL_LENGTH_MM = 18.0
IMAGE_SIZE = 224  # OpenPi's input resolution, so frames need no resizing
VIEWER_EYE = (-1.2, 0.0, 1.0)
VIEWER_TARGET = (0.4, 0.0, 0.1)


def _rgb_obs(camera_name: str) -> ObsTerm:
    return ObsTerm(func=mdp.image_rgb, params={"sensor_cfg": SceneEntityCfg(camera_name), "normalize": False})


@configclass
class CameraShutterSceneCfg(InteractiveSceneCfg):
    """Light, the SCENE_USD fixtures, two Franka arms, the camera prop, and four RGB cameras."""

    light = AssetBaseCfg(
        prim_path="/World/Light", spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=LIGHT_INTENSITY)
    )
    fixtures = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Scene", spawn=sim_utils.UsdFileCfg(usd_path=str(SCENE_USD)))

    robot_left = franka.arm_cfg("RobotLeft", pos=(0.0, ARM_BASE_Y, 0.0), yaw_deg=-90.0)
    robot_right = franka.arm_cfg("RobotRight", pos=(0.0, -ARM_BASE_Y, 0.0), yaw_deg=90.0)

    camera_prop = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/CameraProp",
        spawn=sim_utils.UsdFileCfg(usd_path=str(CAMERA_PROP_USD)),
        init_state=ArticulationCfg.InitialStateCfg(pos=CAMERA_PROP_START, joint_pos={"shutter_joint": 0.0}),
        # Return spring of the shutter button: about 2 N at the full 4 mm press.
        actuators={
            "shutter_spring": ImplicitActuatorCfg(joint_names_expr=["shutter_joint"], stiffness=500.0, damping=5.0)
        },
    )

    table_cam = CameraCfg(
        prim_path="{ENV_REGEX_NS}/TableCam",
        height=IMAGE_SIZE,
        width=IMAGE_SIZE,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=TABLE_CAM_FOCAL_LENGTH_MM, horizontal_aperture=20.955, clipping_range=(0.05, 5.0)
        ),
        offset=CameraCfg.OffsetCfg(
            pos=TABLE_CAM_EYE, rot=frames.look_at_quat(TABLE_CAM_EYE, TABLE_CAM_TARGET), convention="world"
        ),
    )
    left_wrist_cam = franka.wrist_cam_cfg("RobotLeft", image_size=IMAGE_SIZE)
    right_wrist_cam = franka.wrist_cam_cfg("RobotRight", image_size=IMAGE_SIZE)
    # The photo the camera prop would take: a 50 mm lens on 36 mm film, looking along the lens (+x).
    lens_cam = CameraCfg(
        prim_path="{ENV_REGEX_NS}/CameraProp/body/lens_cam",
        height=IMAGE_SIZE,
        width=IMAGE_SIZE,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(focal_length=50.0, horizontal_aperture=36.0, clipping_range=(0.01, 5.0)),
        offset=CameraCfg.OffsetCfg(pos=LENS_FRONT, rot=(0.0, 0.0, 0.0, 1.0), convention="world"),
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
            params={
                "target_pos": SUBJECT_POS,
                "lens_pos_b": LENS_FRONT,
                "asset_cfg": SceneEntityCfg("camera_prop", body_names=["body"]),
            },
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
        params={"minimum_height": CAMERA_DROP_HEIGHT_M, "asset_cfg": SceneEntityCfg("camera_prop")},
    )
    # The photo is taken: the shutter joint goes below SHUTTER_PRESSED_POS, i.e. leaves the bounds below.
    success = DoneTerm(
        func=mdp.joint_pos_out_of_manual_limit,
        params={
            "bounds": (SHUTTER_PRESSED_POS, math.inf),
            "asset_cfg": SceneEntityCfg("camera_prop", joint_names=["shutter_joint"]),
        },
    )


@configclass
class CameraShutterEnvCfg(ManagerBasedRLEnvCfg):
    # env_spacing equals the 5 m floor tile in SCENE_USD, so the floors of cloned envs tile
    # and the table camera does not see the neighbouring envs.
    scene: CameraShutterSceneCfg = CameraShutterSceneCfg(num_envs=NUM_ENVS, env_spacing=5.0)
    observations: ObservationsCfg = ObservationsCfg()
    actions: franka.BimanualActionsCfg = franka.BimanualActionsCfg()
    events: EventsCfg = EventsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    rewards = None
    commands = None
    curriculum = None

    def __post_init__(self):
        self.decimation = PHYSICS_STEPS_PER_ACTION
        self.episode_length_s = EPISODE_LENGTH_S
        self.sim.dt = PHYSICS_DT_S
        self.sim.render_interval = self.decimation
        self.sim.physics = PhysxCfg(
            bounce_threshold_velocity=0.01,
            friction_correlation_distance=0.00625,
            # Let object contacts stall the position-driven grippers before they tunnel through a grasp.
            solve_articulation_contact_last=True,
        )
        self.viewer.eye = VIEWER_EYE
        self.viewer.lookat = VIEWER_TARGET
        self.num_rerenders_on_reset = 3
        scene = self.scene
        for camera_cfg in (scene.table_cam, scene.left_wrist_cam, scene.right_wrist_cam, scene.lens_cam):
            set_isaac_rtx_global_settings(camera_cfg.renderer_cfg, antialiasing_mode="DLAA")
