# FREEZE fast — additional speed preset (`burrow predict --preset fast`)

Feature design `C6m`: grid spacing 1.5 Å, 12 rays, lengths [6.0, 10.0, 16.0] Å, sub-lattice 2, shell ≤ 5.5 Å, PSP length 6.0 Å, metal candidates on; point model 100 trees × 31 leaves, points scored if b ≥ 0.85; pocket link 3.08 Å, min volume 3.0 points; v2 output rule (floor 0.03, min_keep 3). Trained on the D6-audited BioLiP2 train set (same as v2). Not a pre-registered model. Selection and dev numbers: results/dev/biolip/FAST_PRESET.md.

| model | sha256 |
|---|---|
| models/burrow_all_fast_s0.json | 656757b9ccba02fa05d400a831a33f226ad74139ab38d5f0977b26f5ac92f087 |
| models/burrow_small_fast_s0.json | 7b12d3cdd564d3f91833823611e0c62218c5647cb60e68afc433273a2e0ba096 |
| models/burrow_all_fast_s1.json | 10b5b8c18b2a1c0cf5d9fa2ecb47b081200f2f851c06ac2b04c82400d10a83ec |
| models/burrow_small_fast_s1.json | 65d73188e549f9380d49839f9adf672aed2fb70b7486289237e3a22c96ad450c |
| models/burrow_all_fast_s2.json | 8d3a64278fe9eb9b49389955c7500b78e74ae4e59b1ea7a2f241c0c29a6277a4 |
| models/burrow_small_fast_s2.json | 251260fae1a177498c04739eac26cef26f6f594ad760917cc4df87e46d62486f |
