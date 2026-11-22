"""Frame conversions for fixed-base arms. The IK pose actions take targets in the arm's base frame."""

import torch

import isaaclab.utils.math as math_utils
from isaaclab.assets import Articulation


def body_pose_in_base(robot: Articulation, body_name: str) -> torch.Tensor:
    """Pose of `body_name` (xyz + xyzw quaternion) in the robot's base frame, shape (num_envs, 7)."""
    body = robot.find_bodies(body_name)[0][0]
    pos, quat = math_utils.subtract_frame_transforms(
        robot.data.root_pos_w.torch,
        robot.data.root_quat_w.torch,
        robot.data.body_pos_w.torch[:, body],
        robot.data.body_quat_w.torch[:, body],
    )
    return torch.cat([pos, quat], dim=-1)


def point_in_base(robot: Articulation, point_w: torch.Tensor) -> torch.Tensor:
    """World-frame points, shape (num_envs, 3), expressed in the robot's base frame."""
    pos, _ = math_utils.subtract_frame_transforms(robot.data.root_pos_w.torch, robot.data.root_quat_w.torch, point_w)
    return pos
