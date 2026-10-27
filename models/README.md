# Models

All models are JSON files (LightGBM trees + feature design + output settings + provenance), loaded by
`pocketdetect.burrow.model.BurrowModel` (and `pocketdetect.burrow.af_rank.AFRanker` for the AF ranker).
The `burrow` CLI uses the seed-0 file of the selected `--ranker` / `--preset` from this directory
(override the directory with `BURROW_MODELS`, or a single file with `--model`).

| file pattern | what | status |
|---|---|---|
| `burrow_{all,small}_{default,accurate}_s{0,1,2}.json` | FREEZE v2: point scorer + pocket ranker, output floor 0.03 after 3 pockets | pre-registered (docs/PREREG.md); test results in `results/test/v2/` |
| `burrow_{all,small}_fast_s{0,1,2}.json` | `--preset fast` (1.5 Å grid, 12 rays, smaller point model) | added after the tests, not pre-registered (`results/dev/FREEZE_fast.md`) |
| `afr_final_afpdb_pl.json` | optional AF-mode ranker with pLDDT pocket descriptors (`--af-mode --af-ranker models/afr_final_afpdb_pl.json`, reference backend) | optional; recommendation is test-informed (REPORT §4.4) |

Rankers: `all` = sites of ions and organic ligands (LIGYSIS definition); `small` = non-ion small
molecules (P2Rank definition). Seeds: `s0/s1/s2` = `pocketdetect.seeds.SEEDS[:3]`.

## Checksums

`SHA256SUMS` lists the files as shipped (`sha256sum -c SHA256SUMS`). For the release, absolute paths
of the original compute environment were removed from the free-text provenance fields inside `meta`
(e.g. the feature-cache directory); every other field (trees, feature lists, formation/output settings)
is byte-for-byte identical to the frozen research models. The research record (FREEZE_v2.md,
`predictions/MANIFEST.tsv`, `results/test/*/summary.json`) refers to the **original** sha256:

| file | original sha256 (research record) | release sha256 |
|---|---|---|
| afr_final_afpdb_pl.json | `935f887131987021f7ba380a05bef5adc8eac7467dac7a86d9fe524a83404a67` | `a09582f602aab9d551a5d18c30f963e38250ddeb3a1bec6aefa72e4bf8a9b18f` |
| burrow_all_accurate_s0.json | `257df1d8b3595f79d502102ce43755831ee5015fc3d4fe6b49b299aecd44012a` | `76ab42481a151b9a1245fb577a270b3a50661805b728e87a6edffe247b13a423` |
| burrow_all_accurate_s1.json | `145e7ad7d451a2c0ac1541418f1e03351905159821aa309ff0a65c4313861ad5` | `b2b4e21a6ad704c2d60dad096daaff36b76718ffa4fdf638fb030afdf0fae063` |
| burrow_all_accurate_s2.json | `96424bdbe55aaae5749c90cc91692471c6760d1f235842efd4546d5a659a2a59` | `e93bfed7f12ec7d2ba61e18a783772c95f4f842645251c75b9cbc01b6ee7422e` |
| burrow_all_default_s0.json | `0fa4da97c64cc40fb739b87c38372813aa721d52f37a538d3c57dbc8bfc30f56` | `f33963e7e23f1d0b7fd352e89a2dc6b7be30f642cd09ba8644e1967af97c4315` |
| burrow_all_default_s1.json | `317570d46e157c1147634ab35b40ce33f5640a44f1433d5309516e103e9894a9` | `8fbafb6666a2d29ffdf6df31cf1534af1be8d808660e31e8b09fc06865a160fd` |
| burrow_all_default_s2.json | `3e7f1ac500f7bec9322f61510adf7465bc8a79558da3012785cc2057f48acb1e` | `abff3d98c6f47ea82b5b15ec969a40d736508ec4962ba0004ea55cdd8c33117b` |
| burrow_all_fast_s0.json | `656757b9ccba02fa05d400a831a33f226ad74139ab38d5f0977b26f5ac92f087` | `27b1e603270cb160cb538951dd2e0e74660da0351084479fe96757e2dba0b244` |
| burrow_all_fast_s1.json | `10b5b8c18b2a1c0cf5d9fa2ecb47b081200f2f851c06ac2b04c82400d10a83ec` | `bcbb248a0b15a5dc556402f0c9c38bea195835f5ca215a317fb0e4cda37acc2b` |
| burrow_all_fast_s2.json | `8d3a64278fe9eb9b49389955c7500b78e74ae4e59b1ea7a2f241c0c29a6277a4` | `7de81f06d9e18b3d3e26459982daba0f31220d28f88cd93fd727611fce792f03` |
| burrow_small_accurate_s0.json | `0533eb6178728258dc78c28f923800f272c3665668bea4b745203d03e54f0d98` | `9bfc27e23ad94c653273e607391ab071c9daabc7657f1d3f193fad44830fdc93` |
| burrow_small_accurate_s1.json | `9052eb6c0627dd122c0ed217144903a19b8f9a183a7a37565a2085d045fc3414` | `ea350e44980b07ffd5c036b5d91bc2d29a26de5cdee9af5c961d24264bdf2040` |
| burrow_small_accurate_s2.json | `9e2e51489ea2468e8109bc1504c595505deb53989023ba62847d84ed18fcec74` | `ad15c54580fff5c9b5ed5b1cd3b2eabdac3cd37f01c1a431bea8bee8342558e3` |
| burrow_small_default_s0.json | `c0b88419a328332ed8c5c0a2dab3ee2da96aea882001d1ff6aaf20dab8ab34c4` | `cafcfca7e544169224186550e274e1c60f434e0187df2a502ea8424bad6b86e2` |
| burrow_small_default_s1.json | `da798f489b9d843286b08375e50a4a25760b7b477a6e96d8370883554327fa53` | `d4a6cc06abf1c13d5886b3125071c17136f7fb79662a7bfd6d87775aa18cbb3f` |
| burrow_small_default_s2.json | `b770e7227e8f7ea5d12de7eb42dd5cc401c9e0b4bf05de44832a7a68f9e3fd4a` | `41f3248b6d293f599cc7e679e01c6d4eb05b9eb5d8632e882efa636d28fc0538` |
| burrow_small_fast_s0.json | `7b12d3cdd564d3f91833823611e0c62218c5647cb60e68afc433273a2e0ba096` | `2b503fe868863da00879fbdab5e8f3278e7ba4f1797c03331b6b3d09dedba736` |
| burrow_small_fast_s1.json | `65d73188e549f9380d49839f9adf672aed2fb70b7486289237e3a22c96ad450c` | `13a90a621298cb83b0bd5e11065faed537f950aac5ddcc317377b6860e4d01e2` |
| burrow_small_fast_s2.json | `251260fae1a177498c04739eac26cef26f6f594ad760917cc4df87e46d62486f` | `9b5a0e31f7561ba3d115d0d7558230de2b1ad10145ebeadfa685f07d4cab8101` |
