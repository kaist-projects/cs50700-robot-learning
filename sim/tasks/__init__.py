"""Isaac Lab tasks for bimanual manipulation with two Franka arms. Importing this package registers them."""

import gymnasium as gym

CAMERA_SHUTTER_TASK = "Bimanual-CameraShutter-Franka"

gym.register(
    id=CAMERA_SHUTTER_TASK,
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={"env_cfg_entry_point": f"{__name__}.camera_shutter_env_cfg:CameraShutterEnvCfg"},
    disable_env_checker=True,
)
