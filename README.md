# QGIRL Character / See-through Live2D

This public repository is the code and documentation snapshot for the current See-through character workflow. The active source is the See-through-derived front head, with the connected-eye candidate and an isolated native eye-close trial. The old `live2d_v1`–`live2d_v5_1` folders are historical self-split work; they are not the current model.

## Current Stage

- The working open-eye candidate is derived from See-through BeefTV 008, with bilateral eye parts reconnected from run_002 and local lash/brow symmetry. Its PSD is kept in the private working tree and is not uploaded here.
- The separate `eye_close_trial v2` contains native left/right `eye_close` PSD layers beneath `front hair`. Its local PSD SHA256 is `394d9ef9edfc21112c8b94f21a83bd1efdc65f57f9ab12ebbef6215a0c119634`; the user confirmed the visual result on 2026-10-29.
- Anime2.5DRig validation used 20 rig layers and 15 blink poses, including both-eye and independent left/right closure plus small head/brow/bang motion. No synthetic eye-close part was used in that run; neutral restoration was exact and runtime errors were zero.
- The BeefTV source image was RGB with a baked checkerboard. The trial layers were isolated and rebuilt with alpha. The automated report retains `TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED`; user visual approval was received on 2026-10-29.
- Cubism Editor import and binding, CMO3/MOC3 save/reopen, and approximately ±30° head-turn validation remain future work.

The PSD and image captures are deliberately excluded from this code-only repository. The local handoff and full evidence remain in `docs/PROGRESS.md` and `experiments/seethrough_anime25d/` on the workstation.

## Modal Setup

The existing runner is retained at `experiments/seethrough_anime25d/adapters/modal_runner.py`. Clone upstream commit `df019de5129d6c4b406587a14c3501669441a783` into `experiments/seethrough_anime25d/upstream/see-through`, then apply `experiments/seethrough_anime25d/adapters/patches/see-through-head-v2.patch` from that checkout. Prepare a private local `adapters/modal_run_spec.json` from `modal_run_spec.template.json` with only user-authorized input paths. Never commit the private spec or image assets. Read the current local run spec before any explicitly authorized invocation.

## Code Entry Points

| Path | Purpose |
|---|---|
| `experiments/seethrough_anime25d/adapters/modal_runner.py` | Existing Modal runner for the pinned See-through head workflow |
| `experiments/seethrough_anime25d/adapters/prepare_inputs.py` | Pixel-preserving crops from the original multi-view sheet |
| `experiments/seethrough_anime25d/layers/front_eye_poc_006/scripts/test_anime25d.cjs` | Anime2.5DRig runtime validation harness |
| `experiments/seethrough_anime25d/layers/front_eye_poc_006/scripts/validate_assets.py` | Read-only asset validation |
| `experiments/seethrough_anime25d/experiment.json` | Sanitized machine-readable project status |
| `docs/PROGRESS.md` | Current stage, evidence boundary, and next step |
| `REPO_SCOPE.md` | Public snapshot inclusion/exclusion rules |

## Reproducing the Runtime Check

The public snapshot does not vendor upstream projects or character assets. Clone the pinned Anime2.5DRig source into `experiments/seethrough_anime25d/upstream/Anime2.5DRig` at commit `7ddbd9943ea3152561b3dc8348fd752c850f3e95`, provide the local PSD and Playwright installation, then run:

```sh
node experiments/seethrough_anime25d/layers/front_eye_poc_006/scripts/test_anime25d.cjs \
  /path/to/local/eye_close_trial_v2.psd \
  /path/to/local/report-directory
```

This verifies the browser runtime only. It does not create or validate Cubism CMO3/MOC3 files.

## History

The root `live2d_v1`–`live2d_v5_1` directories record the earlier self-split pipeline. Their tests and results remain historical and must not be applied to the See-through candidate. The archived phase1–4 pipeline is indexed in [archive/README.md](archive/README.md).
