"""Camera observation terms that Isaac Lab has no stock term for."""

import torch
from pxr import Usd, UsdGeom

import isaaclab.utils.math as math_utils
from isaaclab.envs import ManagerBasedEnv
from isaaclab.managers import ManagerTermBase, ObservationTermCfg, SceneEntityCfg


class lens_aim_error(ManagerTermBase):
    """Angle in radians between a camera's view axis and the line from the camera to a target prim.

    Params: `sensor_cfg` names the camera, whose view axis is its +x in Isaac Lab's world convention.
    `target_prim` is a prim path relative to each env, such as "Scene/Subject". Its position is read
    once from env 0, so the scene USD stays the only place the target is placed.
    Returns shape (num_envs, 1); 0 means the target sits at the image centre.
    """

    def __init__(self, cfg: ObservationTermCfg, env: ManagerBasedEnv):
        super().__init__(cfg, env)
        self._target_pos_e = _prim_position_in_env(env, cfg.params["target_prim"])

    def __call__(self, env: ManagerBasedEnv, sensor_cfg: SceneEntityCfg, target_prim: str) -> torch.Tensor:
        camera = env.scene[sensor_cfg.name].data
        view_axis = math_utils.quat_apply(camera.quat_w_world.torch, _x_axis(env))
        to_target = env.scene.env_origins + self._target_pos_e - camera.pos_w.torch
        cos_angle = torch.nn.functional.cosine_similarity(view_axis, to_target, dim=-1)
        return torch.acos(cos_angle.clamp(-1.0, 1.0)).unsqueeze(-1)


def _prim_position_in_env(env: ManagerBasedEnv, prim_path_in_env: str) -> torch.Tensor:
    """Position of a prim under env 0, relative to env 0's origin."""
    prim_path = f"{env.scene.env_prim_paths[0]}/{prim_path_in_env}"
    prim = env.sim.stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        raise ValueError(f"Target prim not found: {prim_path}")
    pos_w = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default()).ExtractTranslation()
    return torch.tensor(tuple(pos_w), dtype=torch.float32, device=env.device) - env.scene.env_origins[0]


def _x_axis(env: ManagerBasedEnv) -> torch.Tensor:
    return torch.tensor((1.0, 0.0, 0.0), device=env.device).expand(env.num_envs, 3)
