---
name: sc-pull-cube
description: Pull a cube to a goal position by grasping and dragging it along the surface
tasks: PullCube-v1
---

# Pull Cube

Grasp a cube from above and drag it horizontally to a goal position along the surface.

## Strategy

1. **Grasp from above**: Compute OBB-aligned grasp pose with downward approach
2. **Approach**: Move to offset position 5cm above the grasp point
3. **Grasp**: Move to grasp pose and close gripper
4. **Pull**: Use RRTConnect to drag the cube horizontally to the goal position

## Key Observations

- **Grasp alignment**: OBB-based grasp ensures proper finger orientation
- **Approach offset**: 5cm vertical offset prevents collision during approach
- **Drag motion**: RRTConnect handles large horizontal moves while maintaining grasp
- **Surface contact**: Z offset of 0.02 above goal keeps cube on surface during drag
- **vs Push**: Pull requires closed gripper to hold object; push uses gripper as tool
- **vs Pick**: Pull drags along surface; pick lifts object vertically

## Physical Reasoning

The cube needs to move ~20cm horizontally from its starting position to the goal. By grasping from above and maintaining the grasp during motion, we ensure the cube stays under control throughout the drag motion. The small Z offset prevents the cube from being lifted off the surface while allowing smooth horizontal motion.

## Pattern

```python
# 1. Get OBB and compute grasp
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

## Solved Tasks

- PullCube-v1 (seed=42) ✅
