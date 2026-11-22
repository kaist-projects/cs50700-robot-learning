"""Isaac Lab tasks for bimanual manipulation with two Franka arms, one module per task.

Importing this package registers every task.
"""

import gymnasium as gym

CAMERA_SHUTTER_TASK = "Bimanual-CameraShutter-Franka"

gym.register(
    id=CAMERA_SHUTTER_TASK,
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={"env_cfg_entry_point": f"{__name__}.camera_shutter:CameraShutterEnvCfg"},
    disable_env_checker=True,
)
