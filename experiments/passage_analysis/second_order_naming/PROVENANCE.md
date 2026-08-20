# PROVENANCE

Copied VERBATIM from the read-only archive `github.com/quadrismegistus/malign-logits` at commit

    5c4b5ce60b2685dc0e7083ef8aad5ed858e216de

Nothing under `scripts/` has been edited. Their internal paths refer to the ARCHIVE's layout, so they do not run unmodified from here; that is deliberate, and a run should be a wrapper calling the same design rather than a patched copy.

sha256-verified against the archive at copy time: **17 of 17 match**.

## The corpus is NOT here, and does not need to be

`z_second_order.py` reads `malign_logits.gen_sequences WHERE corpus='f11_l2'` --
228,520 rows, live in ClickHouse, the SAME corpus `../interiority_in_passages/`
uses. Reached by subprocess + clickhouse client.

## `z_second_order.py` exists twice in this repo, deliberately

`../predicting_aligned_text/scripts/` also holds it, because the ascent branch of
`p_on_passages` imports it and that folder is a VERBATIM snapshot of the archive's
state at one commit. This folder is the instrument's home; that one is a frozen
copy. Both are byte-identical to the archive and to each other. If they ever
diverge, this one is right and the snapshot has been edited, which it should not
be.

| file | archive path | bytes | sha256 (16) | note |
| --- | --- | ---: | --- | --- |
| `scripts/z_second_order.py` | `meta/M02_frame_exit/scripts/z_second_order.py` | 14386 | `dc68256bafd584bd` | the marker instrument |
| `scripts/markers_v2.py` | `meta/M02_frame_exit/scripts/markers_v2.py` | 2465 | `751e85070744d2bd` | V2 marker set |
| `scripts/markers_v3.py` | `meta/M02_frame_exit/scripts/markers_v3.py` | 1911 | `f1548c830b599b99` | V3 marker set |
| `scripts/naming_form_control.py` | `meta/M02_frame_exit/scripts/naming_form_control.py` | 6848 | `dbd1344171155d6d` | the form-matched control |
| `scripts/second_order_graded_control.py` | `meta/M02_frame_exit/scripts/second_order_graded_control.py` | 5247 | `ad52934bc5e8a065` |  |
| `scripts/opus_second_order_results.py` | `meta/M02_frame_exit/scripts/opus_second_order_results.py` | 16290 | `2f8b1cc930461341` |  |
| `second_order_naming.md` | `meta/M02_frame_exit/findings/second_order_naming.md` | 31039 | `33b35fa974a3acca` | the finding |
| `naming_survives_form_control.md` | `meta/M02_frame_exit/findings/naming_survives_form_control.md` | 11805 | `529e4d74af2ae290` |  |
| `contradiction_ratio_has_no_null.md` | `meta/M02_frame_exit/findings/contradiction_ratio_has_no_null.md` | 12905 | `709cc7a76fa68ca3` | PROVISIONAL |
| `second_order_markers_v2.md` | `meta/M02_frame_exit/registrations/second_order_markers_v2.md` | 4418 | `eb4ec89a5f38960d` | the registration |
| `results/z_second_order_cells.csv` | `meta/M02_frame_exit/results/z_second_order_cells.csv` | 336663 | `643184e5860d158d` | per-cell |
| `results/naming_form_control.json` | `meta/M02_frame_exit/results/naming_form_control.json` | 42356 | `e5afb3c9d66dc26b` |  |
| `results/opus_second_order_results.json` | `meta/M02_frame_exit/results/opus_second_order_results.json` | 6169 | `add61098ba100da9` |  |
| `results/second_order_exitlex.json` | `meta/M02_frame_exit/results/second_order_exitlex.json` | 3142 | `fe3e5068997a1ad4` |  |
| `results/zh_second_order.json` | `meta/M02_frame_exit/results/zh_second_order.json` | 7604 | `56c17875139b1613` |  |
| `results/l2_exits_without_naming.json` | `meta/M02_frame_exit/results/l2_exits_without_naming.json` | 787 | `ab15f0341901aa92` |  |
| `results/exit_twp_markers.json` | `meta/M02_frame_exit/results/exit_twp_markers.json` | 2771 | `9c3e1b89e827603f` |  |
