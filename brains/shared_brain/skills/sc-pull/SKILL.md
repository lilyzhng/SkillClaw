---
name: sc-pull
description: Pull an object along a surface to a goal position by grasping and dragging horizontally.
---

# Pull

Grasp the object using OBB-aligned approach, then drag it horizontally to the goal position.

## Strategy

1. **Grasp the object** — Use OBB computation to get optimal grasp pose from above
2. **Approach** — Move to pre-grasp pose (5cm above grasp)
3. **Close gripper** — Secure the object
4. **Pull to goal** — Move gripper horizontally to goal position, maintaining grasp height

## Key Observations

- **Pull vs Push**: Pull requires grasping first, then moving. Push uses closed gripper as a tool without grasping.
- **Stay on surface**: Unlike pick tasks that lift, pull keeps the object at the same z-height throughout
- **Use RRTConnect**: The pull motion is typically a large horizontal move (>10cm), so use RRTConnect instead of screw planner
- **Height preservation**: The pull pose uses goal x,y but keeps the grasp pose z-height to maintain contact with surface

## When to Use

- Task name contains "pull"
- Object needs to slide along a surface toward a goal
- Requires maintained contact/grasp during motion

## Difference from Related Skills

- **sc-pick**: Lifts object vertically after grasping
- **sc-push**: No grasping, uses closed gripper to push from behind
- **sc-pull**: Grasps first, then drags horizontally
