# Physics standard (CP77 dangles -> Garry's Mod / PAC3)

CP77 simulates accessories with `animAnimNode_Dangle` + `animDangleConstraint_SimulationDyng` on `dyng_*` bones
(particles, pull forces, link/cone constraints) every frame. That's too heavy to mirror in Gmod, so every dangle
is reduced to the cheapest thing that reads the same in motion:

| CP77 source | Gmod / PAC3 output | Cost rule |
|---|---|---|
| one `dyng_*_01 -> _02` chain (pendulum) | **one PAC `jiggle` part**, the dangling mesh parented under it | 1 jiggle per chain, never per bone |
| `animDyngConstraintCone` half-angle | jiggle `ConstrainAngles` cone (same degrees) | clamp only, no collision |
| `pullForceFactor` (return-to-rest) | jiggle `Strength` = clamp(pull/4, 0.4, 0.9) | |
| particle mass / damping | jiggle `Speed` 0.6-0.8 (heavier = lower) | |
| `animDyngConstraintEllipsoid/Capsule` collision | **dropped** (cone limit stands in) | no per-frame traces |
| chains longer than 3 bones (long hair, tails) | first bone jiggles, rest rigid or a 2-segment jiggle | max 2 jiggles per item |
| simulation LOD (`levelOfDetailStartIndices`) | jiggle hidden when not visible (PAC event `is_in_view`-style culling via `ResetOnHide`) | |

Budget: <= 6 jiggle parts for the whole character. Small items (earrings, pendants) <= 1 each.

## Applied

- **Kwek cross earring (left ear)**: chain `dyng_earring_left_01 -> dyng_earring_left_02`, cone 35 deg (HalfCone),
  pullForceFactor 3.0  ->  1 jiggle: ConstrainAngles 35, Strength 0.75, Speed 0.75, pivot at the hoop (lobe).
  The right earring of the pair is not used (right ear carries the ANRUI cyberware).
