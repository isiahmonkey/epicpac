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
| feet | platform_ankle, tron_red, edgerunner_boots, barefoot |
| neck_jewelry | valentino_cross_silver_rope, none |
| wrist_left | nd_cross_bracelet_silver, none |
| props (separate PAC models) | whiskey_bottle, whiskey_glass_filled |

## PACs and repos
- The outfit sets will be split into **separate PAC files**, one per set. The user will define the sets during PAC setup.
- Multiple GitHub repos are fine, for example one repo per PAC or set. Shared assets (body, head, textures) live once and are referenced.
- Friend-supplied mod files are never hosted publicly (standing rule).
