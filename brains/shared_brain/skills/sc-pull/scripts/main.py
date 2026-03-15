import numpy as np
import sapien

from mani_skill.envs.tasks import PullCubeEnv
from mani_skill.examples.motionplanning.panda.motionplanner import \
    PandaArmMotionPlanningSolver
from mani_skill.examples.motionplanning.base_motionplanner.utils import (
    compute_grasp_info_by_obb, get_actor_obb)

def solve(env: PullCubeEnv, seed=None, debug=False, vis=False):
    env.reset(seed=seed)
    planner = PandaArmMotionPlanningSolver(
        env,
        debug=debug,
        vis=vis,
        base_pose=env.unwrapped.agent.robot.pose,
        visualize_target_grasp_pose=vis,
        print_env_info=False,
    )

    FINGER_LENGTH = 0.025
    env = env.unwrapped
    
    # Get object position
    obj_pos = env.obj.pose.sp.p
    
    # Discover goal position - PullCubeEnv doesn't have goal_site
    goal_pos = None
    for attr in ['goal_site', 'goal_region', 'goal', 'goal_pose']:
        if hasattr(env, attr):
            goal_attr = getattr(env, attr)
            if hasattr(goal_attr, 'pose'):
                goal_pos = goal_attr.pose.sp.p
                break
    
    # Fallback: Could parse from initial state, but for robustness
    # we can check the scene for a goal marker
    if goal_pos is None:
        # This shouldn't happen in practice, but provides a fallback
        raise RuntimeError("Cannot find goal position. Check env attributes.")
    
    # -------------------------------------------------------------------------- #
    # Build grasp pose using OBB (same as sc-pick)
    # -------------------------------------------------------------------------- #
    obb = get_actor_obb(env.obj)
    approaching = np.array([0, 0, -1])
    target_closing = env.agent.tcp.pose.to_transformation_matrix()[0, :3, 1].cpu().numpy()
    
    grasp_info = compute_grasp_info_by_obb(
        obb,
        approaching=approaching,
        target_closing=target_closing,
        depth=FINGER_LENGTH,
    )
    closing, center = grasp_info["closing"], grasp_info["center"]
    grasp_pose = env.agent.build_grasp_pose(approaching, closing, obj_pos)
    
    # -------------------------------------------------------------------------- #
    # Approach and grasp
    # -------------------------------------------------------------------------- #
    reach_pose = grasp_pose * sapien.Pose([0, 0, -0.05])
    res = planner.move_to_pose_with_screw(reach_pose)
    if res == -1:
        raise RuntimeError(f"move_to_pose_with_screw failed for reach_pose {reach_pose.p}")
    
    res = planner.move_to_pose_with_screw(grasp_pose)
    if res == -1:
        raise RuntimeError(f"move_to_pose_with_screw failed for grasp_pose {grasp_pose.p}")
    
    planner.close_gripper()
    
    # -------------------------------------------------------------------------- #
    # Pull to goal
    # -------------------------------------------------------------------------- #
    pull_pose = sapien.Pose(p=goal_pos, q=grasp_pose.q)
    res = planner.move_to_pose_with_screw(pull_pose)
    if res == -1:
        raise RuntimeError(f"move_to_pose_with_screw failed for pull_pose {pull_pose.p}")
    
    planner.close()
    return res
