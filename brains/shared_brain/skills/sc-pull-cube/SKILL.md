---
name: dev-sc-pull-cube
description: Pull a cube to a goal position by grasping and dragging it along the surface
task: PullCube-v1
date: 2026-03-15
status: verified
---

# Pull Cube

Grasp a cube and drag it toward a goal position along a surface.

## Strategy

1. **Open gripper** — prepare for grasping
2. **Approach from the near side** — position gripper on the side of the object closer to its current position (opposite to the pull direction)
3. **Make contact** — move close enough to touch the object with a small offset
4. **Close gripper** — grasp the object
5. **Pull to goal** — drag the object along the surface to the target position

## Key Observations

- **Pull direction**: Object at x=0.0765 needs to move to goal at x=-0.1235 (negative x direction, ~0.2m distance)
- **Approach side**: Approach from positive x side (where object currently is) to pull it in negative x direction
- **Surface constraint**: Maintain the same y and z coordinates during the pull motion
- **Planner selection**: 
  - Use `RRTConnect` for large moves (approach, pull ~20cm)
  - Use `screw` for precision grasp positioning (final contact)
- **Grasp offset**: Position gripper 0.015m offset from cube center for stable grasp
- **Approach offset**: Start 0.04m away from cube for safe approach

## Physical Principles

- The cube stays on the surface throughout the motion (z ≈ 0.02)
- Grasping provides reliable contact for dragging
- The gripper must maintain closed state during the pull to keep the grasp
- Only the x-coordinate changes during pull; y and z remain constant

## Implementation Notes

- Object position: [0.0765, 0.083, 0.02]
- Goal position: [-0.1235, 0.083, 0.001]
- Approach: obj_pos + [0.04, 0, 0]
- Grasp: obj_pos + [0.015, 0, 0]
- Pull target: [goal_x, obj_y, obj_z]
- Success achieved on first attempt with this strategy
