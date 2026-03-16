---
name: dev-sc-pull-cube
description: Pull a cube to a goal position by grasping and dragging it along the surface
task: PullCube-v1
date: 2026-03-15
session: sess_e6deba65
---

# Pull Cube

Pull a cube from its initial position to a goal position by grasping and dragging it along the surface.

## Strategy

1. **Open gripper** — prepare for grasping
2. **Approach from the near side** — position gripper on the side of the object closer to its current position (the positive x side in this case, since we're pulling in the negative x direction)
3. **Make contact** — move close enough to touch the object (offset ~0.015m from center)
4. **Close gripper** — grasp the object
5. **Pull to goal** — drag the object along the surface to the target position

## Key Observations

- **Pull direction**: Object starts at [0.0765, 0.083, 0.02] and needs to reach goal at [-0.1235, 0.083, 0.001] — a pull in the negative x direction (~0.2m distance)
- **Approach side**: Approach from positive x side (where object currently is) and pull toward negative x (where goal is)
- **Surface constraint**: Maintain the same y and z coordinates during the pull motion to keep object on surface
- **Planner selection**: 
  - Use `RRTConnect` for large moves (approach from far, pull motion)
  - Use `screw` for precision grasp positioning (close contact)
- **Grasp positioning**: Small offset from object center (0.015m on +x side) ensures stable grasp

## Physical Principles

- The object stays on the surface throughout the motion
- Grasping provides reliable contact for dragging
- The gripper must maintain closed state during the pull to keep the grasp
- Final position slightly overshoots goal but within tolerance for success

## Implementation Notes

- Approach offset: 0.04m from object center on positive x side
- Grasp offset: 0.015m from object center on positive x side
- Pull target: Use goal x-coordinate, maintain object's y and z coordinates
- Task succeeded on first attempt with reward=1.0
