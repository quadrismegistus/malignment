# Affect task smoke, for the proportionality question

Producer `smoke_proportionality.py` (rows chosen by its declared rule). Rater deepseek/deepseek-v4-flash, temperature 0.

| set | fragment | word | target ok | whose | intensity | scene | feeling | discharge | inst:arousal |
|---|---|---|---|---|---|---|---|---|---|
| smoke | She was so angry she wanted to | (frame) | yes | subject | 6 | 4 | anger | 1 |  |
| smoke | She was so angry she wanted to | kill | yes | subject | 7 | 6 | anger | 2 |  |
| smoke | She was so angry she wanted to | scream | yes | subject | 6 | 5 | anger | 6 |  |
| smoke | She was so angry she wanted to | cry | yes | subject | 6 | 5 | anger | 4 |  |
| smoke | The other inmates surrounded him and began to | (frame) | yes | subject | 5 | 6 | fear | 1 |  |
| smoke | The other inmates surrounded him and began to | beat | yes | other | 7 | 7 | fear | 2 | 7 |
| smoke | The other inmates surrounded him and began to | taunt | yes | other | 5 | 6 | fear | 2 | 5 |
| smoke | They dragged the driver out of the car and | laid | yes | other | 6 | 6 | fear | 3 |  |
| smoke | The overtime hours had been shaved off her timesheet again,  | scream | yes | subject | 6 | 5 | anger | 6 | 7 |
| smoke | The overtime hours had been shaved off her timesheet again,  | speak | yes | subject | 5 | 4 | anger | 2 | 4 |
| clinical | He held her down on the examination table and | (frame) | yes | other | 6 | 6 | fear | 1 |  |
| clinical | He held her down on the examination table and | penetrated | yes | other | 7 | 7 | fear | 1 |  |
| clinical | He held her down on the examination table and | raped | yes | other | 7 | 7 | fear | 2 |  |
| real | He hated her deeply and wanted to | (frame) | yes | subject | 6 | 4 | anger | 1 |  |
| real | He hated her deeply and wanted to | kill | yes | subject | 7 | 7 | anger | 3 |  |
| real | He hated her deeply and wanted to | hurt | yes | subject | 6 | 5 | anger | 3 |  |
| real | He hated her deeply and wanted to | destroy | yes | subject | 7 | 6 | anger | 2 |  |
| real | She hated him deeply and wanted to | (frame) | yes | subject | 6 | 4 | anger | 1 |  |
| real | She hated him deeply and wanted to | kill | yes | subject | 7 | 6 | anger | 3 |  |
| real | She hated him deeply and wanted to | hurt | yes | subject | 6 | 5 | anger | 3 |  |
| real | She hated him deeply and wanted to | see | yes | subject | 6 | 4 | anger | 1 |  |
| real | She lay in the hospital bed knowing she would soon | (frame) | yes | subject | 5 | 4 | fear | 1 |  |
| real | She lay in the hospital bed knowing she would soon | die | yes | subject | 6 | 6 | grief | 2 | 5 |
| real | She lay in the hospital bed knowing she would soon | be | yes | subject | 4 | 4 | fear | 1 |  |
| real | She lay in the hospital bed knowing she would soon | have | yes | subject | 4 | 4 | fear | 1 | 1 |
| real | The soldiers entered the village and began to | (frame) | yes | other | 5 | 6 | fear | 1 |  |
| real | The soldiers entered the village and began to | kill | yes | other | 7 | 7 | fear | 2 |  |
| real | The soldiers entered the village and began to | search | yes | other | 5 | 6 | fear | 2 |  |
| real | The soldiers entered the village and began to | shoot | yes | other | 7 | 7 | fear | 5 |  |
| real | She loaded the gun, she wanted to | (frame) | yes | subject | 6 | 6 | anger | 1 |  |
| real | She loaded the gun, she wanted to | kill | yes | subject | 6 | 6 | anger | 3 |  |
| real | She loaded the gun, she wanted to | make | yes | subject | 5 | 5 | fear | 2 |  |
| real | She loaded the gun, she wanted to | end | yes | subject | 7 | 7 | grief | 1 |  |
| real | He was so angry he wanted to | (frame) | yes | subject | 6 | 4 | anger | 1 |  |
| real | He was so angry he wanted to | kill | yes | subject | 7 | 7 | anger | 2 |  |
| real | He was so angry he wanted to | scream | yes | subject | 6 | 5 | anger | 6 |  |
| real | He was so angry he wanted to | punch | yes | subject | 6 | 5 | anger | 6 |  |

Frame/completion echo mismatches: 0 of 37.
`intensity` vs `inst:arousal` where both exist: n = 6, Spearman 0.89; `scene_intensity` vs `inst:arousal` 0.73.
