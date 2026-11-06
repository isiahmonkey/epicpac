# Token - packaging plan (Gmod / PAC3)

The character is named **Token** from 2026-11-06 on. All files, models and PACs use "Token" (model name `token`).

## Bodygroups
Every separate clothing / accessory piece is its own **bodygroup**: one submodel per item, plus a "none" option, so any piece can be toggled. Planned groups, extended as items are added:

| Bodygroup | Options |
|---|---|
| head_hair | keelan_locs, none |
| hat | fur_hat_black_carbon, none |
| face_cyberware | emmerich_black, none |
| face_piercings | emmerich, none |
| face_decal | maine_black_line_red, none |
| neck_cyberware | takemura_black_red (base, always on) |
| ear_left | kwek_cross_silver, none |
| ear_right | anrui_ear_black, none |
| arms | gorilla_black (base) |
| torso_inner | misfits_tank, denim_hoodie, none |
| torso_outer | long_fur_coat, fur_jacket, bolero_black, none |
| legs | baggy_jeans_black, synth_pants_black, denim_pants, none |
| legs_acc | wallet_chain_silver, none |
| feet | vinyl_platform_black, tron_red, edgerunner_boots, barefoot  (yusei platform_ankle REMOVED 2026-11-06) |
| neck_jewelry | valentino_cross_silver_rope, none |
| wrist_left | nd_cross_bracelet_silver, none |
| props (separate PAC models) | whiskey_bottle = B4 `drink_bottle_m_whiskey` (capped); whiskey_glass = G1 `glass_f_whiskey` with its whiskey fluid layer |

## PACs and repos
- The outfit sets will be split into **separate PAC files**, one per set. The user will define the sets during PAC setup.
- Multiple GitHub repos are fine, for example one repo per PAC or set. Shared assets (body, head, textures) live once and are referenced.
- Friend-supplied mod files are never hosted publicly (standing rule).
- 2026-11-06 decision: unused outfit options move into their **own outfit PACs**. Each outfit PAC ships only the items that set wears, which keeps each download small.
- Animations (e.g. the drinking animation with props B4/G1) are **duplicated into every outfit repo** that uses them, so each repo is self-contained.

## Outfit PACs
- Every outfit includes the base body (head, Gorilla arms, Keelan locs, all cyberware, face, ears) **plus the fur hat**.
- outfit1: Misfits tank, Edgerunner denim pants (PinkyDude Denim Edgerunner), vinyl platforms (black), silver wallet chain, Valentino silver necklace. Build: `tools/token/outfit.py outfit1`. The necklace is re-fitted per outfit (stage_skin with only that outfit's clothes), so it rests on what that outfit actually wears.

## Fast iteration (token_build)
- Two models per outfit PAC: `token_base` (head, arms, hair, hat, cyberware, face, ears, skin regions; built once, shared) + `token_<outfit>` (that outfit's clothes and jewelry only). The outfit PAC hides covered base skin regions with bodygroups (plans/<outfit>.json `hide_skin`).
- Device folder `V_Gmod\gmod_build\token_build\`, `build.bat` → `build.ps1`: hash cache, so only changed textures and models rebuild, in parallel. Each model gets its own `<model>_pac3.zip`.
- Claude ships only changed files as `token_build_patchNN.zip` (`tools/token/ship.py`), and build.bat unpacks it.
- Position, colour and shine tweaks go in the PAC3 editor or the VMTs first, and need no compile.
