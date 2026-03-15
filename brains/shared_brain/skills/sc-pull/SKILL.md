---
date: 2026-03-15
time: 13:49

name: sc-pull
description: Pull an object to a goal position by grasping and dragging it horizontally.
---

# Pull

Pull an object to a goal by grasping from above and dragging it along the surface.

## Strategy

1. **Grasp from above**: Use OBB-aligned grasp approaching from top
2. **Close gripper**: Secure the object
3. **Drag to goal**: Move horizontally to goal position while maintaining grasp height

## Key Observations

- Pull is essentially a horizontal "pick" - grasp the object and move it without lifting
- Keep the z-coordinate at object height to maintain contact with surface during drag
- Use RRTConnect for initial approach (large move), screw for precision grasp and pull
- Goal position can be extracted from initial state if env doesn't have goal_site attribute

## Pattern

```python
# Grasp from above (same as pick)
grasp_pose = env.agent.build_grasp_pose(approaching, closing, obj_pos)
approach_pose = grasp_pose * sapien.Pose([0, 0, -0.05])

# Move and grasp
planner.move_to_pose_with_RRTConnect(approach_pose)
planner.move_to_pose_with_screw(grasp_pose)
planner.close_gripper()

# Drag horizontally to goal (NOT lifting)
pull_pose = sapien.Pose(p=[goal_x, goal_y, obj_z], q=grasp_pose.q)
planner.move_to_pose_with_screw(pull_pose)
```

## Difference from Push

- **Push**: Gripper behind object, no grasp, push forward
- **Pull**: Gripper above object, grasp required, drag to goal

## Tasks Solved

- PullCube-v1 (seed=42)
