---
name: dev-sc-pull-cube
description: Pull a cube to a goal position by grasping and dragging it along the surface
task: PullCube-v1
date: 2026-03-15
session: sess_0688552e
seed: 42
---

# Pull Cube

Pull a cube from its starting position to a goal position by grasping and dragging it along the surface.

## Strategy

1. **Open gripper** — prepare for grasping
2. **Approach from the far side** — position gripper on the side of the object opposite to the pull direction (if pulling in -X direction, approach from +X side)
3. **Move to grasp position** — get close enough to make contact with the object
4. **Close gripper** — grasp the object firmly
5. **Pull to goal** — drag the object along the surface to the target position

## Key Observations

- **Approach side matters**: To pull an object from position A to position B, approach from side A (the starting side) and drag toward B
- **Surface constraint**: Maintain the same z-height (surface level) during the pull motion to keep object on table
- **Goal position**: PullCube-v1 provides goal position from initial state, typically in negative X direction
- **Planner selection**: 
  - Use `RRTConnect` for large moves (approach, pull motion)
  - Use `screw` for precise grasp positioning
- **Offset positioning**: Approach with ~0.04m offset, grasp at ~0.015m offset from cube center

## Physical Principles

- The object remains on the surface throughout the motion
- Grasping provides reliable contact for dragging vs pushing
- Gripper must stay closed during pull to maintain grasp
- Final position achieved: object at [-0.1374, 0.0834, 0.021], goal at [-0.1235, 0.083, 0.001]

## Implementation Notes

- TCP orientation stays constant (gripper pointing down)
- Only X coordinate changes during pull, Y and Z remain constant
- Success achieved on first attempt with this strategy
