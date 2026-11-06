// collect_face_options.wscript  -  STAGING: every character-creator face tattoo, piercing and makeup option (male) + their meshes/textures
// Pulls these base-game files AND everything they reference (layer templates, textures) into the ACTIVE project.
// Run: Tools -> Script Manager -> this script -> Run. Takes a few minutes.
const Logger = { Info: m=>logger.Info(m), Success: m=>logger.Success(m) };

const MOD_DEPS = [
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_01.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_04.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_05.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_06.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_07.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_08.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_09.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_10.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_11.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_12.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_13.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_14.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_15.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_16.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_17.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_18.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_19.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_20.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_21.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_22.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_23.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_24.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_25.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_26.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_27.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_28.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_29.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_30.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_31.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_32.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_33.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_34.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_35.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_eyes\\hx_000__basehead_makeup_eyes_36.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_01.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_04.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_05.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_06.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_07.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_08.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_09.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_10.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_11.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_12.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_13.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_14.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_15.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_16.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_17.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_18.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_19.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_cheeks_20.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_freckles_01.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_freckles_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_freckles_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_freckles\\hx_000__basehead_makeup_freckles_04.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_01.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_01_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_01_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_02_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_02_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_03_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_03_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_04.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_04_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_04_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_05.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_05_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_05_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_06.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_06_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_06_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_07.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_07_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_07_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_08.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_08_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_08_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_09.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_09_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_09_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_10.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_10_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_10_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_11.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_11_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_11_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_12.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_12_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_12_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_13.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_13_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_13_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_14.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_14_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_14_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_15.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_15_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_15_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_16.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_16_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_16_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_17.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_17_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_17_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_18.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_18_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_18_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_19.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_19_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_19_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_20.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_20_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_20_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_21.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_21_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_21_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_22.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_22_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_22_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_23.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_23_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_23_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_24.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_24_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_24_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_25.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_25_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_25_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_26.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_26_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_26_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_27_nicola.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_27_nicola_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_27_nicola_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_28.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_28_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_28_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_29_trauma.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_29_trauma_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_29_trauma_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_30.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_30_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_30_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_31.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_31_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_31_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_32.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_32_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_32_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_33.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_33_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_33_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_34_avante.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_34_avante_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_34_avante_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_35_mox.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_35_mox_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_35_mox_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_36_jinguji.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_36_jinguji_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_36_jinguji_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_37_6thstreet.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_37_6thstreet_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_37_6thstreet_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_38_budgetarms.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_38_budgetarms_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\makeup_lips\\hx_000__basehead_makeup_lips_38_budgetarms_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_01.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_04.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_05.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_06.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_07.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_08.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_09.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_10.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_11.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_12.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_13.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_14.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_15.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\piercings\\i0_000__earring_16.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\pimples\\hx_000__basehead_pimples_01.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\pimples\\hx_000__basehead_pimples_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\pimples\\hx_000__basehead_pimples_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_01.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_02.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_03.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_04.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_05.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_06.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_07.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_08.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_09.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_10.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_11.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_12.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_13.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_14.app",
  "base\\characters\\head\\player_base_heads\\appearances\\head\\tattoos\\hx_000__tattoo_15.app"
];

const WALK_EXT  = ['mesh','mi','mt','mlsetup','mltemplate','app','ent','inkcc','remt'];
const SKIP_EXT  = ['anims','animgraph','workspot','scene','physicalscene','cookedapp','fb2tl','wem','bk2','streamingsector','streamingblock','csv','json'];

function ext(p){ const i=p.lastIndexOf('.'); return i<0?'':p.substring(i+1).toLowerCase(); }
function isFemale(p){ return /pwa|player_woman|woman_base|_wa_|\\wa_|_pwa_/.test(p); }
function isMale(p){ return /pma|player_man|man_base/.test(p) && !isFemale(p); }

function seedFromPatterns(){
  const seeds=[];
  const e = wkit.GetArchiveFiles().GetEnumerator();
  let n=0;
  while (e.MoveNext()){
    const f=e.Current; if(!f) continue;
    const p=(''+f.FileName).toLowerCase(); n++;
    const x=ext(p);
    if (SKIP_EXT.indexOf(x)>=0) continue;
    if (p.startsWith('base\\characters\\head\\') && isMale(p)) seeds.push(p);
    else if (p.startsWith('base\\characters\\common\\player_base_bodies\\') && isMale(p)) seeds.push(p);
    else if (p.startsWith('base\\characters\\cyberware\\') && !isFemale(p) && /pma|player|\\ma_|_ma_/.test(p)) seeds.push(p);
    else if (x==='inkcc') seeds.push(p);
    else if (x==='rig' && isMale(p)) seeds.push(p);
  }
  Logger.Info('Scanned '+n+' game files, '+seeds.length+' pattern matches');
  return seeds;
}

function depsOf(p){
  if (WALK_EXT.indexOf(ext(p))<0) return [];
  let j=null;
  try { j = wkit.GetFileFromArchive(p, OpenAs.Json); } catch(err) { return []; }
  if (!j) return [];
  const out=[]; const re=/"((?:base|engine|ep1)(?:\\\\[^"\\\\]+)+\.[a-z0-9_]+)"/gi; let m;
  while ((m=re.exec(''+j))!==null){ out.push(m[1].replace(/\\\\/g,'\\').toLowerCase()); }
  return out;
}

const queue = MOD_DEPS.map(s=>s.toLowerCase());
const seen = {}; const added=[]; const missing=[];
while (queue.length){
  const p=queue.shift();
  if (seen[p]) continue; seen[p]=true;
  if (p.indexOf('{')>=0 || p.indexOf('*')>=0) continue;
  const x=ext(p); if (SKIP_EXT.indexOf(x)>=0) continue;
  if (!wkit.FileExistsInArchive(p)) { missing.push(p); continue; }
  wkit.Extract(p); added.push(p);
  if (added.length % 200 === 0) Logger.Info('...added '+added.length+' files');
  for (const d of depsOf(p)) if (!seen[d] && !/pwa|player_woman|woman_base/.test(d)) queue.push(d);
}
wkit.SaveToRaw('collect_face_options_manifest.txt', 'ADDED '+added.length+'\n'+added.join('\n')+'\n\nMISSING '+missing.length+'\n'+missing.join('\n'));
Logger.Success('Done. Added '+added.length+' files ('+missing.length+' not found). Manifest: source\\raw\\collect_face_options_manifest.txt');
