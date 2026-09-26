# Cleaning the polar Warriner valence lexicon of ambiguous words (EXPLORATORY)

Producer `valence_lexicon_clean.py` (standard and design in its docstring). Per item: /Users/rj416/malignment-data/interiority_norms/valence_clean_keep_v1_pos.csv.

- pass 1 vs pass 2 agreement on keep: 89.5%; ties rejected: 0; batches dropped for flipped anchors: 0 of 264

- CALIBRATION, LLM valence vs Warriner on 4 polar lemmas: Spearman 0.949, Pearson 0.976, mean |diff| 0.53; on kept lemmas only: Spearman 1.000
- largest LLM-above-Warriner gaps (period or sense shift?): old 4.0/3.2, late 4.0/3.3, sunshine 8.0/8.1, murder 1.0/1.5
- largest LLM-below-Warriner gaps: murder 1.0/1.5, sunshine 8.0/8.1, late 4.0/3.3, old 4.0/3.2

- polar lemmas: 4 rated, 2 kept (50%); rejections by reason: competing_neutral_sense 2
- mapped forms: 0 rated, 0 kept (nan%); rejections by reason: 
- vector negative-pole candidates: 0 rated, 0 kept (nan%); rejections by reason: 
- vector positive-pole candidates: 4998 rated, 798 kept (16%); rejections by reason: proper_name 2122, competing_neutral_sense 1193, other 776, clear_connotation 42, function_like 30, wrong_direction 30, mapping_mismatch 6, period_shift 1

Rejected negative lemmas (sample): old (competing_neutral_sense); late (competing_neutral_sense)

Rejected positive lemmas (sample): 

Vector candidates kept (most frequent first is not available here; alphabetical sample): abloom 7.5, acacia 7.0, acacias 7.0, accolade 8.0, acme 7.2, adaptability 6.5, adaptable 7.0, admirably 7.5, adorably 8.0, adorn 7.5, adorned 7.2, adorning 7.0, adornment 7.0, adornments 7.2, adorns 7.0, affability 7.5, affable 7.5, affectionately 8.0, affectionateness 8.0, afterglow 7.5, ageless 7.0, agreeableness 7.5, agreeably 7.5, aigrette 6.8, airy 7.0, alacrity 7.2, alleluia 8.0, alluringly 7.2, amaranth 7.0, amaryllis 7.0, ambrosial 8.0, amenity 7.0, amiably 7.5, amply 7.0, anemones 7.0, angelical 8.0, angelically 8.0, antiquity 6.5, appreciatively 7.2, approbation 7.5, arbors 7.0, arbour 7.0, arcadia 8.0, aromatic 7.0, asphodel 6.8, attainments 7.0, attar 7.0, attentiveness 7.0, attractively 7.5, attractiveness 7.5, aureola 7.0, aurora 7.5, auspiciously 7.5, autumnal 6.5, azaleas 7.0, azure 7.0, beamingly 8.0, beamy 7.0, beatific 8.0, beatitude 8.0

Rejected mapped forms (sample): 
