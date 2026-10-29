# Current Progress and Handoff

Updated: 2026-10-29 (Hong Kong time). The current line is the See-through-derived front character; the earlier self-split versions are historical.

## Latest Candidate

The See-through BeefTV 008 head was connected to the run_002 open-eye parts and locally balanced for lash/brow symmetry. The separate eye-close trial adds two native eye-close layers under `front hair` while retaining the open-eye layers for runtime switching. The PSD remains local; its hash and evidence are recorded in the sanitized experiment summary.

The source eye-close PNG was RGB and contained a baked checkerboard. The two line components were isolated, scaled proportionally to about 70%, and rebuilt as transparent layer candidates. This removes the baked background but also loses grayscale antialiasing detail. The user reviewed the result on 2026-10-29 and confirmed it looks good.

## Verification

- Anime2.5DRig upstream commit: `7ddbd9943ea3152561b3dc8348fd752c850f3e95`.
- 20 runtime rig layers; 15 blink poses; bilateral closure and independent screen-left/screen-right closure.
- Small head, brow, and bang movement capture completed.
- Native eye-close roles: 2; runtime-synthesized eye-close roles: 0.
- Neutral pose restored exactly; unknown layer count 0; page and console errors 0.
- Technical report status: `TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED`; user visual approval: received 2026-10-29. Runtime evidence is based on static captures, not continuous playback or Cubism validation.

## Code in This Snapshot

- Existing Modal runner and input preparation utility are under `experiments/seethrough_anime25d/adapters/`.
- The Anime2.5DRig validation harness and its configuration are under `experiments/seethrough_anime25d/layers/front_eye_poc_006/`.
- Upstream checkouts, PSDs, generated PNGs, and full screenshots are excluded by `REPO_SCOPE.md`.
- `modal_run_spec.json` is private and is not published. Use the safe template only after preparing a local, user-authorized configuration.

## Next Step

Prepare a Cubism import candidate and validate import, binding, and parameter editing in Cubism Editor. CMO3/MOC3 reopen and approximately ±30° head-turn occlusion tests come after that.
