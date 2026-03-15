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
    
    # Get object and goal positions
    obj_pos = env.obj.pose.sp.p
    goal_pos = env.goal_region.pose.sp.p
    
    # Compute grasp pose using OBB
    obb = get_actor_obb(env.obj)
    approaching = np.array([0, 0, -1])  # approach from above
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
    # Approach
    # -------------------------------------------------------------------------- #
    reach_pose = grasp_pose * sapien.Pose([0, 0, -0.05])
    res = planner.move_to_pose_with_screw(reach_pose)
    if res == -1:
        raise RuntimeError(f"Failed to reach approach pose at {reach_pose.p}")
    
    # -------------------------------------------------------------------------- #
    # Grasp
    # -------------------------------------------------------------------------- #
    res = planner.move_to_pose_with_screw(grasp_pose)
    if res == -1:
        raise RuntimeError(f"Failed to reach grasp pose at {grasp_pose.p}")
    
    planner.close_gripper()
    
    # -------------------------------------------------------------------------- #
    # Pull to goal
    # -------------------------------------------------------------------------- #
    # Keep same height (don't lift), just change x,y position to goal
    pull_pose = sapien.Pose(
        p=[goal_pos[0], goal_pos[1], grasp_pose.p[2]], 
        q=grasp_pose.q
    )
    
    # Use RRTConnect for large horizontal motion
    res = planner.move_to_pose_with_RRTConnect(pull_pose)
    if res == -1:
        raise RuntimeError(f"Failed to pull to goal at {pull_pose.p}")
    
    planner.close()
    return res
