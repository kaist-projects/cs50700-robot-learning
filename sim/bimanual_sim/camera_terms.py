"""Camera-prop observation terms that Isaac Lab has no stock term for."""

import torch

import isaaclab.utils.math as math_utils
from isaaclab.envs import ManagerBasedEnv
from isaaclab.managers import SceneEntityCfg

LENS_AXIS_B = (1.0, 0.0, 0.0)  # the lens points along +x of the camera prop's body


def lens_aim_error(
    env: ManagerBasedEnv,
    target_pos: tuple[float, float, float],
    lens_pos_b: tuple[float, float, float],
    asset_cfg: SceneEntityCfg,
) -> torch.Tensor:
    """Angle in radians between the lens axis and the line from the lens to `target_pos`.

    `target_pos` is in the env frame and `lens_pos_b` in the frame of the body in `asset_cfg`.
    Returns shape (num_envs, 1); 0 means the target sits at the image centre.
    """
    camera = env.scene[asset_cfg.name]
    body = asset_cfg.body_ids[0]
    body_pos = camera.data.body_pos_w.torch[:, body] - env.scene.env_origins
    body_quat = camera.data.body_quat_w.torch[:, body]
    lens_pos = body_pos + math_utils.quat_apply(body_quat, _per_env(env, lens_pos_b))
    lens_axis = math_utils.quat_apply(body_quat, _per_env(env, LENS_AXIS_B))
    cos_angle = torch.nn.functional.cosine_similarity(lens_axis, _per_env(env, target_pos) - lens_pos, dim=-1)
    return torch.acos(cos_angle.clamp(-1.0, 1.0)).unsqueeze(-1)


def _per_env(env: ManagerBasedEnv, vec: tuple[float, float, float]) -> torch.Tensor:
    return torch.tensor(vec, dtype=torch.float32, device=env.device).expand(env.num_envs, 3)
