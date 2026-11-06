# STAGING manifest — Takemura Hades Edition V

Source preset: `takemura hades edition.preset` (40 options, resolved against `male_cco.inkcharcustomization`).

| Slot | Choice | Source |
|---|---|---|
| Head mesh | Hades Edition head (re-sculpted, 6,864 verts) | Hades_Edition_Takemura_Cyberware__Head |
| Face shape | PANTHEON_MASC_DIONYSUS: eyes h111, nose h122, mouth h143, jaw h144, ear h025 (was Hades: eyes h141, nose h102, mouth h143, jaw h034) (vanilla deltas transferred by nearest vertex) | base morphs |
| Neck cyberware | Takemura neck (57k verts, multilayered), recoloured black + red (iron/steel/titanium layers -> black, red enamel kept) | Hades_Edition_Takemura_Cyberware__Head |
| Skin | deep brown (darker than CC 06_bl_dark; overrides preset pale), skin type 01 detail (basehead_d01); alt 06_bl_dark | base |
| Eyes | eye_14 (overrides preset eye colour) | HighTech_Eyes_pack |
| Brows | style 08, black_carbon | base |
| Scars | face scar 02 | base |
| Face cyberware | Emmerich CC cyberware_13 (cheek/eye + nose/chin plates), repainted gloss black (was pearl chrome) | base CC |
| Face circuit lines | ANRUI Maine (MeshM), Black Line / Red accents, OG metal/rough/normal; drawn under the Emmerich plates | ANRUI_Maine_Cyberware |
| Face piercing | Emmerich CC piercings 03 (nose rings + lip), plastic_black, rigid per ring | base CC |
| Earring | Kwek simple cross earrings (earrings_06) kwek_silver, LEFT ear only, dangle -> 1 PAC jiggle (standards/physics.md) | kwekClothing_Earrings06 |
| Ear cyberware | RIGHT ear only (left gets the cross earring); ANRUI ear shell, Black, metal full / rough half / OG normals; skin tucked under, lifted over neck piece | ANRUI_MEarCyberware_Base + Customization |
| Hair | Half Bun Dreads (Male V), black_carbon (overrides preset hair) | Half_Bun_DreadsMale_V |
| Body | player_man_average base body (censored skin) + HQ arms + natural nails, graded to the head deep tone | base |
| Arms | Gorilla Arms x2 (TPP holstered), BLACK: fingers + knuckle plating gloss black, decals darkened, red details kept; organic nails removed | base cyberware |
| Fur jacket | axellysse fur jacket (jacket_fur_m_base_body), black_carbon fur cards; hoodie hidden | axellysse_fur_collection |
| Hoodie (hidden) | PinkyDude Denim Edgerunner t1 hoodie (pma base_body), shared 4k atlas (metal_base: d/m/r/n/e) | PinkyDude_Clothes_DenimEdgerunnerSet |
| Pants | Denim Edgerunner l1 pants | PinkyDude_Clothes_DenimEdgerunnerSet |
| Chain | Denim Edgerunner i1 thigh chain (right hip) | PinkyDude_Clothes_DenimEdgerunnerSet |
| Shoes | yusei Platform Ankle Boots (short_heeled_boots) black, pma; body feet chunk hidden | short_heeled_boots |
| Hat | axellysse fur hat (hat_fur_m_base_body.mesh), black_carbon fur cards (hh_short01 + black_carbon.hp); inner cap material pending collect_staging2 | axellysse_fur_collection |
| Coat (maybe) | axellysse fur jacket, black_carbon | axellysse_fur_collection |
| Teeth / nails / lashes | defaults | base |

## Update: tattoos, Synth Pants, boots
- **Tattoo:** VTK MALVINA (all 4 layers), moved from the Female V body/arm UVs onto the male base body and arms. Each body part is mapped onto the matching male part by scaling its bounding box, then snapped to the male surface. Ink is about 90% opacity, so it reads as healed black ink.
- **Legs:** Synth Pants, default appearance (the plain black item, `synth_black_basic`). Final: real Militech l1_078 mask set and normal map, layered with the cotton weave detail normal.
- **Feet:** Denim Edgerunner boots, `s1_pma_denimedgerunner_boots`. The yusei platform boots are hidden, not removed.
- **Hidden:**
  - Edgerunner pants
  - wallet chain (the silver re-finish is ready)
  - hoodie
  - fur hat (`SHOW_HAT=0`)
- **Fur jacket:** the real black_carbon material.
  - Strands use the hair profile gradient: near-black roots to warm grey-brown tips.
  - The under-layer uses the black_carbon cap gradient-map recolour of the t1_104 fur detail texture.
  - Frizz:
    - ragged, broken strand tips and per-strand value variation;
    - a sparse second card layer lifted 3 mm with flyaways at the tips;
    - scattered, weak highlights plus a fibre-edge fuzz term.
  - PAC note: the frizz layer adds about 45% more fur-card triangles.
