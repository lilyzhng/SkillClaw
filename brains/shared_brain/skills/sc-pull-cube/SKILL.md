---
name: dev-sc-pull-cube
description: Pull a cube to a goal position by grasping and dragging it along the surface
task: PullCube-v1
seed: 42
date: 2026-03-15
---

# Pull Cube

Pull a cube from its initial position to a goal location by grasping and dragging it horizontally along the surface.

## Strategy

1. **Grasp from above**: Use OBB-aligned grasp pose approaching from above (z-axis = -1)
2. **Approach and close**: Move to approach pose (5cm above), then to grasp pose, then close gripper
3. **Drag to goal**: Use RRTConnect to move horizontally to goal position while maintaining grasp

## Key Observations

- **Grasp stability**: Top-down grasp from above provides stable grip for horizontal dragging
- **Z-offset critical**: Pull pose needs small Z offset (0.02m) above goal to keep cube on surface without lifting
- **Large move planner**: RRTConnect handles the ~20cm horizontal drag motion robustly
- **Orientation preservation**: Maintaining the same gripper orientation (grasp_pose.q) during pull prevents twisting

## Physical Reasoning

This is a **pull** task (not push or pick):
- Object must move from initial position (x=0.077) to goal (x=-0.123) = ~20cm in -X direction
- Pull = grasp + drag (unlike push which uses closed gripper as tool without grasping)
- Keeping object on surface requires precise Z control (not lifting like pick tasks)

## Pattern

```python
# 1. Compute OBB grasp from above
approaching = np.array([0, 0, -1])
grasp_info = compute_grasp_info_by_obb(obb, approaching, target_closing, depth=FINGER_LENGTH)
grasp_pose = env.agent.build_grasp_pose(approaching, closing, obj_pos)

# 2. Approach and grasp
approach_pose = grasp_pose * sapien.Pose([0, 0, -0.05])
planner.move_to_pose_with_screw(approach_pose)
planner.move_to_pose_with_screw(grasp_pose)
planner.close_gripper()

# 3. Pull to goal
pull_pose = sapien.Pose(p=goal_pos + np.array([0, 0, 0.02]), q=grasp_pose.q)
planner.move_to_pose_with_RRTConnect(pull_pose)
```

## Results

- **Task**: PullCube-v1 (seed=42)
- **Success**: ✓ (reward=1.0, task_success=true)
- **Final position**: x=-0.1189 (goal=-0.1235, error=0.0046m)
- **Attempts**: 1 (worked on first try)
