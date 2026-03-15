---
name: dev-sc-pull-cube
description: Pull a cube to a goal position by grasping and dragging it along the surface
task: PullCube-v1
seed: 42
session: sess_478fee26
---

# Pull Cube

Successfully pulls a cube from its initial position to a goal position by grasping it and dragging it horizontally along the surface.

## Strategy

1. **Compute OBB-aligned grasp** - Use the object's oriented bounding box to determine optimal grasp pose approaching from above
2. **Approach and grasp** - Move to approach pose (5cm above grasp), then to grasp pose, then close gripper
3. **Pull to goal** - Use RRTConnect to drag the grasped cube horizontally to the goal position (keeping Z slightly above goal to maintain surface contact)

## Key Observations

- **Grasp from above**: Approaching from top (z-axis) provides stable grasp for horizontal pulling motion
- **RRTConnect for pull**: Large horizontal moves (20cm in this case) require RRTConnect planner, not screw
- **Height management**: Pull pose Z is set to `goal_z + 0.02` to keep cube on surface during drag
- **Orientation preservation**: Pull pose maintains the same orientation (quaternion) as grasp pose

## Physical Reasoning

Pull differs from push and pick:
- **vs Push**: Pull grasps the object (gripper closed around it), push uses closed gripper as a flat paddle
- **vs Pick**: Pull keeps object near surface during horizontal motion, pick lifts object vertically first

The cube needs to be held securely during the pull motion, so grasping is essential.

## Code Pattern

```python
# 1. Compute grasp from OBB
obb = get_actor_obb(env.obj)
grasp_info = compute_grasp_info_by_obb(obb, approaching, target_closing, depth)
grasp_pose = env.agent.build_grasp_pose(approaching, closing, obj_pos)

# 2. Approach and grasp
approach_pose = grasp_pose * sapien.Pose([0, 0, -0.05])
planner.move_to_pose_with_screw(approach_pose)
planner.move_to_pose_with_screw(grasp_pose)
planner.close_gripper()

# 3. Pull to goal
pull_pose = sapien.Pose(p=goal_pos + [0, 0, 0.02], q=grasp_pose.q)
planner.move_to_pose_with_RRTConnect(pull_pose)
```

## Result

- Initial cube position: [0.0765, 0.083, 0.02]
- Goal position: [-0.1235, 0.083, 0.001]
- Final cube position: [-0.1189, 0.083, 0.0219]
- Distance traveled: ~20cm in negative X direction
- Task success: ✅ True
- Reward: 1.0

## Video

demos/PullCube-v1_sess_478fee26.mp4
