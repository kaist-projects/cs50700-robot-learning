"""Shared Franka Panda robot, wrist camera, and 16D bimanual IK/gripper action configs and helpers."""

import math
from pathlib import Path

import torch

import isaaclab.envs.mdp as mdp
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg
from isaaclab.controllers.differential_ik_cfg import DifferentialIKControllerCfg
from isaaclab.envs import ManagerBasedRLEnv
from isaaclab.envs.mdp.actions.actions_cfg import DifferentialInverseKinematicsActionCfg
from isaaclab.sensors import CameraCfg
from isaaclab.utils import configclass

from isaaclab_assets.robots.franka import FRANKA_PANDA_HIGH_PD_CFG  # isort: skip

from common import frames

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
FRANKA_USD = ASSET_DIR / "franka_panda" / "panda_instanceable.usd"

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


def arm_cfg(prim_name: str, pos: tuple[float, float, float], yaw_deg: float) -> ArticulationCfg:
    """Franka Panda with its hand, loaded from the local asset copy and placed at `pos`."""
    return FRANKA_PANDA_HIGH_PD_CFG.replace(
        prim_path=f"{{ENV_REGEX_NS}}/{prim_name}",
        spawn=FRANKA_PANDA_HIGH_PD_CFG.spawn.replace(usd_path=str(FRANKA_USD)),
        init_state=FRANKA_PANDA_HIGH_PD_CFG.init_state.replace(
            pos=pos, rot=frames.yaw_quat(yaw_deg), joint_pos=FRANKA_READY_JOINT_POS
        ),
    )


def wrist_cam_cfg(robot_prim_name: str, image_size: int) -> CameraCfg:
    """Wrist camera on panda_hand, using the mount pose of Isaac Lab's Franka visuomotor task."""
    return CameraCfg(
        prim_path=f"{{ENV_REGEX_NS}}/{robot_prim_name}/panda_hand/wrist_cam",
        height=image_size,
        width=image_size,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(focal_length=24.0, horizontal_aperture=20.955, clipping_range=(0.05, 3.0)),
        offset=CameraCfg.OffsetCfg(
            pos=(0.13, 0.0, -0.15), rot=(0.03701, 0.03701, -0.70614, -0.70614), convention="ros"
        ),
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
class BimanualActionsCfg:
    """16D action, in this order: left hand pose 7, left gripper 1, right hand pose 7, right gripper 1."""

    left_arm = _hand_pose_action("robot_left")
    left_gripper = _gripper_action("robot_left")
    right_arm = _hand_pose_action("robot_right")
    right_gripper = _gripper_action("robot_right")


GRIPPER_OPEN, GRIPPER_CLOSE = 1.0, -1.0
LEFT_HAND_POSE, RIGHT_HAND_POSE = slice(0, 7), slice(8, 15)  # where each hand pose sits in the 16D action


def compose_action(
    left_pose: torch.Tensor, left_gripper: float, right_pose: torch.Tensor, right_gripper: float
) -> torch.Tensor:
    """Concatenate a 16D action in BimanualActionsCfg order from (num_envs, 7) hand poses and gripper commands."""
    gripper = lambda value: torch.full((left_pose.shape[0], 1), value, device=left_pose.device)  # noqa: E731
    return torch.cat([left_pose, gripper(left_gripper), right_pose, gripper(right_gripper)], dim=-1)


def hold_current_pose_action(env: ManagerBasedRLEnv) -> torch.Tensor:
    """16D action that keeps both hands where they are, with both grippers open."""
    left_pose = frames.body_pose_in_base(env.scene["robot_left"], "panda_hand")
    right_pose = frames.body_pose_in_base(env.scene["robot_right"], "panda_hand")
    return compose_action(left_pose, GRIPPER_OPEN, right_pose, GRIPPER_OPEN)
