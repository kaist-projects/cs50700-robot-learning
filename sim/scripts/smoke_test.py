"""Smoke test for the camera-shutter env.

Holds both hands still, presses the shutter button with the right hand and lifts it again, then
prints IK tracking error, the shutter joint travel, and observation shapes. One frame per camera is
saved at the deepest press.

Run from the repository root in the `isaacsim` conda env:

    PYTHONPATH=sim python sim/scripts/smoke_test.py
    PYTHONPATH=sim python sim/scripts/smoke_test.py --viz kit --keep_open   # GUI window
"""

import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Smoke test for the bimanual camera-shutter env.")
parser.add_argument("--out_dir", default="sim/outputs/smoke", help="Directory for the saved camera frames.")
parser.add_argument(
    "--keep_open", action="store_true", help="After the test, hold the hands still until the app window is closed."
)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_overrides = parser.parse_known_args()
simulation_app = AppLauncher(args_cli, enable_cameras=True).app

from pathlib import Path  # noqa: E402

import imageio.v3 as iio  # noqa: E402
import torch  # noqa: E402

import bimanual_sim  # noqa: E402
import isaaclab.utils.math as math_utils  # noqa: E402
from isaaclab.envs import ManagerBasedRLEnv  # noqa: E402
from isaaclab_tasks.utils import parse_env_cfg  # noqa: E402

CAMERA_TERMS = ("table_cam", "left_wrist_cam", "right_wrist_cam")
OPEN, CLOSE = 1.0, -1.0
FINGERTIP_BELOW_HAND = 0.1034  # panda_hand origin to fingertip, with the hand pointing down
BUTTON_TOP_ABOVE_ORIGIN = 0.0048  # the button link origin is the bottom of the button head
APPROACH_HEIGHT = 0.05
PRESS_DEPTH = 0.01  # how far past the button top the fingertips are commanded
PHASE_STEPS = 40  # 2 s at 20 Hz


def main():
    env = ManagerBasedRLEnv(cfg=parse_env_cfg(bimanual_sim.CAMERA_SHUTTER_TASK, num_envs=1, overrides=hydra_overrides))
    env.reset()

    hold = hold_current_pose_action(env)
    step_for(env, hold, PHASE_STEPS)
    report_tracking_error(env, hold)

    above_button, into_button = shutter_press_actions(env, hold)
    step_for(env, above_button, PHASE_STEPS)
    obs = step_for(env, into_button, PHASE_STEPS)
    pressed = shutter_position(env)
    save_camera_frames(obs["policy"], Path(args_cli.out_dir))
    step_for(env, above_button, PHASE_STEPS)
    released = shutter_position(env)
    print(f"[smoke] shutter joint: pressed {pressed * 1e3:.1f} mm, released {released * 1e3:.1f} mm")

    print_observation_shapes(obs["policy"])
    if args_cli.keep_open:
        hold_until_app_closes(env, hold_current_pose_action(env))
    env.close()


def hold_until_app_closes(env: ManagerBasedRLEnv, hold: torch.Tensor) -> None:
    while simulation_app.is_running():
        env.step(hold)


def hold_current_pose_action(env: ManagerBasedRLEnv) -> torch.Tensor:
    return compose_action(hand_pose_in_base(env, "robot_left"), OPEN, hand_pose_in_base(env, "robot_right"), OPEN)


def shutter_press_actions(env: ManagerBasedRLEnv, hold: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Right-hand targets above the button and past its top, fingers closed, orientation unchanged."""
    left_pose, right_pose = hold[:, 0:7], hold[:, 8:15]
    button_top_w = shutter_button_top(env)
    actions = []
    for fingertip_offset in (APPROACH_HEIGHT, -PRESS_DEPTH):
        hand_target_w = button_top_w + torch.tensor([0.0, 0.0, FINGERTIP_BELOW_HAND + fingertip_offset], device=env.device)
        target_pose = torch.cat([point_in_base(env, "robot_right", hand_target_w), right_pose[:, 3:7]], dim=-1)
        actions.append(compose_action(left_pose, OPEN, target_pose, CLOSE))
    return actions[0], actions[1]


def report_tracking_error(env: ManagerBasedRLEnv, commanded: torch.Tensor) -> None:
    for name, pose_slice in (("robot_left", slice(0, 3)), ("robot_right", slice(8, 11))):
        error = torch.linalg.norm(hand_pose_in_base(env, name)[:, :3] - commanded[:, pose_slice], dim=-1)
        print(f"[smoke] {name} hold position error: {error[0].item() * 1e3:.2f} mm")


def step_for(env: ManagerBasedRLEnv, action: torch.Tensor, steps: int) -> dict:
    for _ in range(steps):
        obs, *_ = env.step(action)
    return obs


def compose_action(left_pose, left_gripper: float, right_pose, right_gripper: float) -> torch.Tensor:
    """Concatenate the 16D action in the env's term order."""
    gripper = lambda value: torch.full((left_pose.shape[0], 1), value, device=left_pose.device)  # noqa: E731
    return torch.cat([left_pose, gripper(left_gripper), right_pose, gripper(right_gripper)], dim=-1)


def hand_pose_in_base(env: ManagerBasedRLEnv, robot_name: str) -> torch.Tensor:
    """panda_hand pose (xyz + xyzw quaternion) in the robot's base frame, the frame the IK action uses."""
    robot = env.scene[robot_name]
    hand = robot.find_bodies("panda_hand")[0][0]
    pos, quat = math_utils.subtract_frame_transforms(
        robot.data.root_pos_w.torch,
        robot.data.root_quat_w.torch,
        robot.data.body_pos_w.torch[:, hand],
        robot.data.body_quat_w.torch[:, hand],
    )
    return torch.cat([pos, quat], dim=-1)


def point_in_base(env: ManagerBasedRLEnv, robot_name: str, point_w: torch.Tensor) -> torch.Tensor:
    robot = env.scene[robot_name]
    pos, _ = math_utils.subtract_frame_transforms(robot.data.root_pos_w.torch, robot.data.root_quat_w.torch, point_w)
    return pos


def shutter_button_top(env: ManagerBasedRLEnv) -> torch.Tensor:
    camera_prop = env.scene["camera_prop"]
    button = camera_prop.find_bodies("shutter_button")[0][0]
    return camera_prop.data.body_pos_w.torch[:, button] + torch.tensor([0.0, 0.0, BUTTON_TOP_ABOVE_ORIGIN], device=env.device)


def shutter_position(env: ManagerBasedRLEnv) -> float:
    """Shutter joint position in metres: 0 released, -0.004 fully pressed."""
    return env.scene["camera_prop"].data.joint_pos.torch[0, 0].item()


def print_observation_shapes(policy_obs: dict[str, torch.Tensor]) -> None:
    for name, value in policy_obs.items():
        print(f"[smoke] obs {name}: {tuple(value.shape)}")


def save_camera_frames(policy_obs: dict[str, torch.Tensor], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in CAMERA_TERMS:
        path = out_dir / f"{name}.png"
        iio.imwrite(path, policy_obs[name][0].cpu().numpy().astype("uint8"))
        print(f"[smoke] saved {path}")


if __name__ == "__main__":
    main()
    simulation_app.close()
