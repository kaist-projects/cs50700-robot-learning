"""Bimanual camera-shutter environment: two fixed-base Franka arms and a camera with a pressable shutter.

World frame: +x points from the arms toward the subject, +y to the left, z = 0 is the table top.
The left arm (+y) holds the camera and the right arm (-y) presses the shutter button. Both arms
face the table centre. Stock Isaac Lab MDP terms are used, except the lens aim error in
camera_terms.py.
"""

import math
from pathlib import Path

from isaaclab_physx.physics import PhysxCfg

import isaaclab.envs.mdp as mdp
import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.controllers.differential_ik_cfg import DifferentialIKControllerCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.envs.mdp.actions.actions_cfg import DifferentialInverseKinematicsActionCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import CameraCfg
from isaaclab.utils import configclass

from isaaclab_tasks.utils.presets import set_isaac_rtx_global_settings

from isaaclab_assets.robots.franka import FRANKA_PANDA_HIGH_PD_CFG  # isort: skip

from . import camera_terms

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
FRANKA_USD = ASSET_DIR / "franka_panda" / "panda_instanceable.usd"
CAMERA_PROP_USD = ASSET_DIR / "camera_prop" / "camera.usda"

TABLE_SIZE = (1.4, 1.4, 0.75)
TABLE_CENTER = (0.3, 0.0, -TABLE_SIZE[2] / 2)
ARM_BASE_Y = 0.5
CAMERA_PROP_START = (0.35, 0.15, 0.001)  # prop origin is its bottom centre
LENS_FRONT = (0.071, 0.0099, 0.0338)  # 1 mm ahead of the lens glass, in the camera prop's body frame
SUBJECT_POS = (0.9, 0.0, 0.15)
TABLE_CAM_EYE = (-0.3, 0.0, 1.5)
TABLE_CAM_TARGET = (0.4, 0.0, 0.05)
IMAGE_SIZE = 224  # OpenPi's input resolution, so frames need no resizing
# libfranka's "ready" pose, with the hand pointing straight down. Isaac Lab's default tilts it by 45 degrees.
FRANKA_READY_JOINT_POS = {
    "panda_joint1": 0.0,
    "panda_joint2": -math.pi / 4,
    "panda_joint3": 0.0,
    "panda_joint4": -3 * math.pi / 4,
    "panda_joint5": 0.0,
    "panda_joint6": math.pi / 2,
    "panda_joint7": math.pi / 4,
    "panda_finger_joint.*": 0.04,
}


def _yaw_quat(yaw_deg: float) -> tuple[float, float, float, float]:
    """Return the xyzw quaternion for a rotation about +z."""
    half = math.radians(yaw_deg) / 2
    return (0.0, 0.0, math.sin(half), math.cos(half))


def _look_at_quat(eye, target) -> tuple[float, float, float, float]:
    """Return the xyzw quaternion that points a world-convention camera (+x forward, +z up) at target."""
    dx, dy, dz = (t - e for t, e in zip(target, eye))
    half_yaw = math.atan2(dy, dx) / 2
    half_pitch = math.atan2(-dz, math.hypot(dx, dy)) / 2
    cy, sy = math.cos(half_yaw), math.sin(half_yaw)
    cp, sp = math.cos(half_pitch), math.sin(half_pitch)
    return (-sy * sp, cy * sp, sy * cp, cy * cp)


def _franka_cfg(prim_name: str, base_y: float, yaw_deg: float) -> ArticulationCfg:
    """Franka Panda with its hand, loaded from the local asset copy and placed on the table top."""
    return FRANKA_PANDA_HIGH_PD_CFG.replace(
        prim_path=f"{{ENV_REGEX_NS}}/{prim_name}",
        spawn=FRANKA_PANDA_HIGH_PD_CFG.spawn.replace(usd_path=str(FRANKA_USD)),
        init_state=FRANKA_PANDA_HIGH_PD_CFG.init_state.replace(
            pos=(0.0, base_y, 0.0), rot=_yaw_quat(yaw_deg), joint_pos=FRANKA_READY_JOINT_POS
        ),
    )


def _wrist_cam_cfg(robot_prim_name: str) -> CameraCfg:
    """Wrist camera on panda_hand, using the mount pose of Isaac Lab's Franka visuomotor task."""
    return CameraCfg(
        prim_path=f"{{ENV_REGEX_NS}}/{robot_prim_name}/panda_hand/wrist_cam",
        height=IMAGE_SIZE,
        width=IMAGE_SIZE,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(focal_length=24.0, horizontal_aperture=20.955, clipping_range=(0.05, 3.0)),
        offset=CameraCfg.OffsetCfg(
            pos=(0.13, 0.0, -0.15), rot=(0.03701, 0.03701, -0.70614, -0.70614), convention="ros"
        ),
    )


def _rgb_obs(camera_name: str) -> ObsTerm:
    return ObsTerm(
        func=mdp.image, params={"sensor_cfg": SceneEntityCfg(camera_name), "data_type": "rgb", "normalize": False}
    )


@configclass
class CameraShutterSceneCfg(InteractiveSceneCfg):
    """Table, two Franka arms, the camera prop, a subject to aim at, and four RGB cameras."""

    floor = AssetBaseCfg(
        prim_path="/World/Floor",
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, -TABLE_SIZE[2] - 0.01)),
        spawn=sim_utils.CuboidCfg(
            size=(8.0, 8.0, 0.02),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.4, 0.4, 0.42)),
        ),
    )
    light = AssetBaseCfg(
        prim_path="/World/Light", spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=2000.0)
    )
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        init_state=AssetBaseCfg.InitialStateCfg(pos=TABLE_CENTER),
        spawn=sim_utils.CuboidCfg(
            size=TABLE_SIZE,
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.55, 0.42, 0.3)),
        ),
    )
    # Visual-only target the camera should aim at (no collision properties).
    subject = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Subject",
        init_state=AssetBaseCfg.InitialStateCfg(pos=SUBJECT_POS),
        spawn=sim_utils.CylinderCfg(
            radius=0.04, height=0.3, visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.1, 0.6, 0.2))
        ),
    )

    robot_left = _franka_cfg("RobotLeft", base_y=ARM_BASE_Y, yaw_deg=-90.0)
    robot_right = _franka_cfg("RobotRight", base_y=-ARM_BASE_Y, yaw_deg=90.0)

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
        spawn=sim_utils.PinholeCameraCfg(focal_length=18.0, horizontal_aperture=20.955, clipping_range=(0.05, 5.0)),
        offset=CameraCfg.OffsetCfg(
            pos=TABLE_CAM_EYE, rot=_look_at_quat(TABLE_CAM_EYE, TABLE_CAM_TARGET), convention="world"
        ),
    )
    left_wrist_cam = _wrist_cam_cfg("RobotLeft")
    right_wrist_cam = _wrist_cam_cfg("RobotRight")
    # The photo the camera prop would take: a 50 mm lens on 36 mm film, looking along the lens (+x).
    lens_cam = CameraCfg(
        prim_path="{ENV_REGEX_NS}/CameraProp/body/lens_cam",
        height=IMAGE_SIZE,
        width=IMAGE_SIZE,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(focal_length=50.0, horizontal_aperture=36.0, clipping_range=(0.01, 5.0)),
        offset=CameraCfg.OffsetCfg(pos=LENS_FRONT, rot=(0.0, 0.0, 0.0, 1.0), convention="world"),
    )


def _hand_pose_action(robot_name: str) -> DifferentialInverseKinematicsActionCfg:
    """Absolute panda_hand pose target (xyz + xyzw quaternion) in the arm's base frame, solved by IK."""
    return DifferentialInverseKinematicsActionCfg(
        asset_name=robot_name,
        joint_names=["panda_joint.*"],
        body_name="panda_hand",
        controller=DifferentialIKControllerCfg(command_type="pose", use_relative_mode=False, ik_method="dls"),
    )


def _gripper_action(robot_name: str) -> mdp.BinaryJointPositionActionCfg:
    """One gripper command: negative closes, zero or positive opens."""
    return mdp.BinaryJointPositionActionCfg(
        asset_name=robot_name,
        joint_names=["panda_finger.*"],
        open_command_expr={"panda_finger_.*": 0.04},
        close_command_expr={"panda_finger_.*": 0.0},
    )


@configclass
class ActionsCfg:
    """16D action, in this order: left hand pose 7, left gripper 1, right hand pose 7, right gripper 1."""

    left_arm = _hand_pose_action("robot_left")
    left_gripper = _gripper_action("robot_left")
    right_arm = _hand_pose_action("robot_right")
    right_gripper = _gripper_action("robot_right")


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
            func=camera_terms.lens_aim_error,
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
        func=mdp.root_height_below_minimum, params={"minimum_height": -0.1, "asset_cfg": SceneEntityCfg("camera_prop")}
    )


@configclass
class CameraShutterEnvCfg(ManagerBasedRLEnvCfg):
    scene: CameraShutterSceneCfg = CameraShutterSceneCfg(num_envs=1, env_spacing=3.0)
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    events: EventsCfg = EventsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    rewards = None
    commands = None
    curriculum = None

    def __post_init__(self):
        # 100 Hz physics, 20 Hz control: the rate of OpenPi's Franka pre-training data.
        self.decimation = 5
        self.episode_length_s = 30.0
        self.sim.dt = 0.01
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
