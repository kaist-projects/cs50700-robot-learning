"""Frame conversions and xyzw orientation quaternions for fixed-base arms and cameras."""

import math
from collections.abc import Sequence

import torch

import isaaclab.utils.math as math_utils
from isaaclab.assets import Articulation


def yaw_quat(yaw_deg: float) -> tuple[float, float, float, float]:
    """Return the xyzw quaternion for a rotation about +z."""
    half = math.radians(yaw_deg) / 2
    return (0.0, 0.0, math.sin(half), math.cos(half))


def look_at_quat(eye: Sequence[float], target: Sequence[float]) -> tuple[float, float, float, float]:
    """Return the xyzw quaternion that points a world-convention camera (+x forward, +z up) at target."""
    dx, dy, dz = (t - e for t, e in zip(target, eye))
    half_yaw = math.atan2(dy, dx) / 2
    half_pitch = math.atan2(-dz, math.hypot(dx, dy)) / 2
    cy, sy = math.cos(half_yaw), math.sin(half_yaw)
    cp, sp = math.cos(half_pitch), math.sin(half_pitch)
    return (-sy * sp, cy * sp, sy * cp, cy * cp)


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
