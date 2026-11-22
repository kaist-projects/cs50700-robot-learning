"""Build the camera-shutter env, hold the default pose for a few steps, and save one frame per camera.

Run from the repository root in the `isaacsim` conda env:

    PYTHONPATH=sim python sim/scripts/smoke_test.py
"""

import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Smoke test for the bimanual camera-shutter env.")
parser.add_argument("--steps", type=int, default=30, help="Environment steps to run before saving frames.")
parser.add_argument("--out_dir", default="sim/outputs/smoke", help="Directory for the saved camera frames.")
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_overrides = parser.parse_known_args()
simulation_app = AppLauncher(args_cli, enable_cameras=True).app

from pathlib import Path  # noqa: E402

import imageio.v3 as iio  # noqa: E402
import torch  # noqa: E402

import bimanual_sim  # noqa: E402
from isaaclab.envs import ManagerBasedRLEnv  # noqa: E402
from isaaclab_tasks.utils import parse_env_cfg  # noqa: E402

CAMERA_TERMS = ("table_cam", "left_wrist_cam", "right_wrist_cam")


def main():
    env_cfg = parse_env_cfg(bimanual_sim.CAMERA_SHUTTER_TASK, num_envs=1, overrides=hydra_overrides)
    env = ManagerBasedRLEnv(cfg=env_cfg)
    obs, _ = env.reset()
    hold_default_pose = torch.zeros_like(env.action_manager.action)
    for _ in range(args_cli.steps):
        obs, *_ = env.step(hold_default_pose)
    print_observation_shapes(obs["policy"])
    save_camera_frames(obs["policy"], Path(args_cli.out_dir))
    env.close()


def print_observation_shapes(policy_obs: dict[str, torch.Tensor]) -> None:
    for name, value in policy_obs.items():
        summary = "" if name in CAMERA_TERMS else f" {value[0].cpu().numpy().round(3).tolist()}"
        print(f"[smoke] {name}: {tuple(value.shape)}{summary}")


def save_camera_frames(policy_obs: dict[str, torch.Tensor], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in CAMERA_TERMS:
        path = out_dir / f"{name}.png"
        iio.imwrite(path, policy_obs[name][0].cpu().numpy().astype("uint8"))
        print(f"[smoke] saved {path}")


if __name__ == "__main__":
    main()
    simulation_app.close()
