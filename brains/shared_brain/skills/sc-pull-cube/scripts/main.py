import numpy as np
import sapien

def solve(env, planner):
    """
    Pull a cube to a goal position by grasping and dragging it along the surface.
    
    Strategy:
    1. Open gripper
    2. Approach from the far side (positive X to pull in negative X direction)
    3. Move to grasp position
    4. Close gripper
    5. Pull to goal position
    """
    env = env.unwrapped
    
    # Get object and goal positions
    obj_pos = env.obj.pose.sp.p
    
    # Goal position (try different attributes)
    if hasattr(env, 'goal_site'):
        goal_pos = env.goal_site.pose.sp.p
    elif hasattr(env, 'goal_region'):
        goal_pos = env.goal_region.pose.sp.p
    else:
        # Fallback: use heuristic for PullCube (goal typically in negative x)
        goal_pos = np.array([-0.1235, obj_pos[1], 0.001])
    
    # Use current TCP orientation (gripper pointing down)
    tcp_quat = env.agent.tcp.pose.sp.q
    
    # -------------------------------------------------------------------------- #
    # Open gripper and approach from positive x side (to pull in -x direction)
    # -------------------------------------------------------------------------- #
    planner.open_gripper()
    
    # Approach from the side closer to object current position (positive x)
    approach_pos = obj_pos + np.array([0.04, 0, 0])
    approach_pose = sapien.Pose(p=approach_pos, q=tcp_quat)
    res = planner.move_to_pose_with_RRTConnect(approach_pose)
    if res == -1:
        raise RuntimeError(f"move_to_pose_with_RRTConnect failed for approach position {approach_pos}")
    
    # -------------------------------------------------------------------------- #
    # Move to grasp position and close gripper
    # -------------------------------------------------------------------------- #
    grasp_pos = obj_pos + np.array([0.015, 0, 0])
    grasp_pose = sapien.Pose(p=grasp_pos, q=tcp_quat)
    res = planner.move_to_pose_with_screw(grasp_pose)
    if res == -1:
        raise RuntimeError(f"move_to_pose_with_screw failed for grasp position {grasp_pos}")
    
    planner.close_gripper()
    
    # -------------------------------------------------------------------------- #
    # Pull to goal position
    # -------------------------------------------------------------------------- #
    # Maintain same y and z, only change x to goal
    pull_target = np.array([goal_pos[0], obj_pos[1], obj_pos[2]])
    pull_pose = sapien.Pose(p=pull_target, q=tcp_quat)
    res = planner.move_to_pose_with_RRTConnect(pull_pose)
    if res == -1:
        raise RuntimeError(f"move_to_pose_with_RRTConnect failed for pull to {pull_target}")
    
    return res
