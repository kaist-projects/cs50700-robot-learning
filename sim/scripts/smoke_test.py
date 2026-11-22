"""Smoke test for the camera-shutter env.

Holds both hands still, presses the shutter button with the right hand and lifts it again. Prints
the lens aim error, the shutter joint travel with the success check, and the observation shapes,
and saves one frame per camera at the deepest press.

Run from the repository root in the `isaacsim` conda env:

    PYTHONPATH=sim python sim/scripts/smoke_test.py
    PYTHONPATH=sim python sim/scripts/smoke_test.py --viz kit --keep_open   # GUI window
"""

import argparse
import math

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

from isaaclab.envs import ManagerBasedRLEnv  # noqa: E402
from isaaclab.managers import TerminationTermCfg as DoneTerm  # noqa: E402
from isaaclab_tasks.utils import parse_env_cfg  # noqa: E402
import tasks  # noqa: E402
from common import frames  # noqa: E402
from tasks.camera_shutter import (  # noqa: E402
    GRIPPER_CLOSE,
    GRIPPER_OPEN,
    LEFT_HAND_POSE,
    RIGHT_HAND_POSE,
    compose_action,
    hold_current_pose_action,
)

CAMERA_TERMS = ("table_cam", "left_wrist_cam", "right_wrist_cam", "lens_cam")
FINGERTIP_BELOW_HAND = 0.1034  # panda_hand origin to fingertip, with the hand pointing down
BUTTON_TOP_ABOVE_ORIGIN = 0.0048  # the button link origin is the bottom of the button head
APPROACH_HEIGHT = 0.05
PRESS_DEPTH = 0.01  # how far past the button top the fingertips are commanded
PHASE_STEPS = 40  # 2 s at 20 Hz


def main():
    env, success_term = make_env()
    env.reset()

    hold = hold_current_pose_action(env)
    obs = step_for(env, hold, PHASE_STEPS)
    report_aim_error(obs["policy"])

    above_button, into_button = shutter_press_actions(env, hold)
    step_for(env, above_button, PHASE_STEPS)
    pressed = step_for(env, into_button, PHASE_STEPS)["policy"]
    pressed_success = is_success(env, success_term)
    save_camera_frames(pressed, Path(args_cli.out_dir))
    released = step_for(env, above_button, PHASE_STEPS)["policy"]
    report_shutter(pressed, pressed_success, released, is_success(env, success_term))

    print_observation_shapes(pressed)
    if args_cli.keep_open:
        hold_until_app_closes(env, hold_current_pose_action(env))
    env.close()


def make_env() -> tuple[ManagerBasedRLEnv, DoneTerm]:
    """Build the env with its success term taken out, as record_demos.py does, so a press does not reset it."""
    env_cfg = parse_env_cfg(tasks.CAMERA_SHUTTER_TASK, num_envs=1, overrides=hydra_overrides)
    success_term, env_cfg.terminations.success = env_cfg.terminations.success, None
    return ManagerBasedRLEnv(cfg=env_cfg), success_term


def is_success(env: ManagerBasedRLEnv, success_term: DoneTerm) -> bool:
    return bool(success_term.func(env, **success_term.params)[0])


def hold_until_app_closes(env: ManagerBasedRLEnv, hold: torch.Tensor) -> None:
    while simulation_app.is_running():
        env.step(hold)


def shutter_press_actions(env: ManagerBasedRLEnv, hold: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Right-hand targets above the button and past its top, fingers closed, orientation unchanged."""
    left_pose, right_pose = hold[:, LEFT_HAND_POSE], hold[:, RIGHT_HAND_POSE]
    button_top_w = shutter_button_top(env)
    actions = []
    for fingertip_offset in (APPROACH_HEIGHT, -PRESS_DEPTH):
        hand_target_w = button_top_w + torch.tensor([0.0, 0.0, FINGERTIP_BELOW_HAND + fingertip_offset], device=env.device)
        target_pose = torch.cat([frames.point_in_base(env.scene["robot_right"], hand_target_w), right_pose[:, 3:7]], dim=-1)
        actions.append(compose_action(left_pose, GRIPPER_OPEN, target_pose, GRIPPER_CLOSE))
    return actions[0], actions[1]


def report_aim_error(policy_obs: dict[str, torch.Tensor]) -> None:
    print(f"[smoke] lens aim error: {math.degrees(policy_obs['lens_aim_error'][0, 0].item()):.1f} deg")


def report_shutter(pressed: dict, pressed_success: bool, released: dict, released_success: bool) -> None:
    """Print the shutter joint travel (0 released, -4 mm fully pressed) and the success check at each end."""
    pressed_mm, released_mm = (obs["shutter_pos"][0, 0].item() * 1e3 for obs in (pressed, released))
    print(f"[smoke] shutter joint: pressed {pressed_mm:.1f} mm (success {pressed_success}), "
          f"released {released_mm:.1f} mm (success {released_success})")


def step_for(env: ManagerBasedRLEnv, action: torch.Tensor, steps: int) -> dict:
    for _ in range(steps):
        obs, *_ = env.step(action)
    return obs


def shutter_button_top(env: ManagerBasedRLEnv) -> torch.Tensor:
    camera_prop = env.scene["camera_prop"]
    button = camera_prop.find_bodies("shutter_button")[0][0]
    return camera_prop.data.body_pos_w.torch[:, button] + torch.tensor([0.0, 0.0, BUTTON_TOP_ABOVE_ORIGIN], device=env.device)


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
