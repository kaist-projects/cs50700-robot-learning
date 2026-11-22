"""Smoke test for the camera-shutter env."""

from isaaclab.app import AppLauncher

simulation_app = AppLauncher(enable_cameras=True).app

from isaaclab.envs import ManagerBasedRLEnv  # noqa: E402
from isaaclab_tasks.utils import parse_env_cfg  # noqa: E402

import tasks  # noqa: E402
from common.franka import hold_current_pose_action  # noqa: E402

env = ManagerBasedRLEnv(cfg=parse_env_cfg(tasks.CAMERA_SHUTTER_TASK))
env.reset()
action = hold_current_pose_action(env)
for _ in range(10):
    env.step(action)
env.close()
simulation_app.close()
