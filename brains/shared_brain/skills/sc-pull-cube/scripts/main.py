import numpy as np
import sapien

def solve(env, planner):
    """
    Pull a cube to a goal position by grasping and dragging it along the surface.
    
    Strategy:
    1. Compute OBB-aligned grasp pose (approaching from above)
    2. Approach and grasp the object
    3. Drag it horizontally to the goal position using RRTConnect
    """
    env = env.unwrapped
    
    FINGER_LENGTH = 0.025
    
    # Get object oriented bounding box
    obb = get_actor_obb(env.obj)
    
    # Compute grasp pose approaching from above
    approaching = np.array([0, 0, -1])
    target_closing = env.agent.tcp.pose.to_transformation_matrix()[0, :3, 1].cpu().numpy()
    
    grasp_info = compute_grasp_info_by_obb(
        obb,
        approaching=approaching,
        target_closing=target_closing,
        depth=FINGER_LENGTH,
    )
    
    closing, center = grasp_info["closing"], grasp_info["center"]
    grasp_pose = env.agent.build_grasp_pose(approaching, closing, env.obj.pose.sp.p)
    
    # -------------------------------------------------------------------------- #
    # Approach and grasp
    # -------------------------------------------------------------------------- #
    # Approach pose (5cm above grasp)
    reach_pose = grasp_pose * sapien.Pose([0, 0, -0.05])
    res = planner.move_to_pose_with_screw(reach_pose)
    if res == -1:
        raise RuntimeError(f"Failed to reach approach pose at {reach_pose.p}")
    
    # Move to grasp pose
    res = planner.move_to_pose_with_screw(grasp_pose)
    if res == -1:
        raise RuntimeError(f"Failed to reach grasp pose at {grasp_pose.p}")
    
    # Close gripper to grasp
    planner.close_gripper()
    
    # -------------------------------------------------------------------------- #
    # Pull to goal
    # -------------------------------------------------------------------------- #
    # Get goal position from environment
    goal_pos = env.goal_site.pose.sp.p if hasattr(env, 'goal_site') else env.goal_region.pose.sp.p
    
    # Create pull pose: keep the same orientation, move to goal position
    # The Z coordinate should be slightly above the goal to keep the cube on the surface
    pull_pose = sapien.Pose(p=goal_pos + np.array([0, 0, 0.02]), q=grasp_pose.q)
    
    # Use RRTConnect for large horizontal move
    res = planner.move_to_pose_with_RRTConnect(pull_pose)
    if res == -1:
        raise RuntimeError(f"Failed to pull to goal position {pull_pose.p}")
    
    planner.close()
    return res
