---
name: sc-pull
description: Pull an object to a goal position by grasping and dragging horizontally
task: PullCube-v1
seed: 42
session: sess_d9a216c7
---

# Pull

Grasp object from above → move horizontally to goal position.

## Strategy

1. **Grasp**: Use OBB-aligned grasp from above (same as sc-pick)
2. **Pull**: Move TCP to goal position while maintaining grasp
3. **Result**: Object follows gripper to goal

## Key Observations

- Pull is essentially a horizontal version of Pick (Pick lifts vertically, Pull moves horizontally)
- No special "dragging" physics needed - standard motion planning works
- Screw planner handles 0.2m horizontal moves with grasped objects without issues
- Goal position discovery: PullCubeEnv doesn't have `goal_site` - try common attribute names or use initial state fallback

## Differences from Push

- **Push**: Closed gripper as tool, no grasping, push from behind
- **Pull**: Grasp first, then move gripper with object held

## Pattern

```python
# 1. Grasp (from sc-pick)
grasp_pose = build_grasp_pose(...)
approach → grasp → close_gripper()

# 2. Pull to goal
pull_pose = sapien.Pose(p=goal_pos, q=grasp_pose.q)
planner.move_to_pose_with_screw(pull_pose)
```

## When to Use

- Task name contains "pull"
- Object must move horizontally along surface to goal
- Object needs to be held during motion (vs pushed without grasping)
