# L-CUNLOAD2 tiny compatibility review

16 cells / 50 DOF, no workpiece. Actual new test records only; not circle grip evidence.

|series|d mm|R N|relative residual|fresh anchor|
|---|---:|---:|---:|---|
|A0_load|0.0|0.0|0.0|False|
|A0_load|0.00025|0.00014196564343962474|9.563002893791295e-10|False|
|A0_load|0.0005|0.00028394341759967705|4.783000621192142e-10|False|
|A1_load_append|0.0005|0.00028394341759967705|4.783000621192142e-10|True|
|A1_load_append|0.00075|0.0004259333215026563|3.18967332795584e-10|False|
|A2_first_unload|0.00075|0.0004259333215026563|3.18967332795584e-10|True|
|A2_first_unload|0.0005|0.000283943417599676|4.776594086682374e-10|False|
|A3_cycle_append|0.0005|0.000283943417599676|4.776594086682374e-10|True|
|A3_cycle_append|0.00025|0.00014196564343962369|9.550180892688135e-10|False|
|B0_old_cycle|0.0|0.0|0.0|False|
|B0_old_cycle|0.0005|0.0002839434176028183|1.3066749305489284e-15|False|
|B0_old_cycle|0.00025|0.0001419656434396237|9.550179688053108e-10|False|
|B1_old_cycle_append|0.00025|0.0001419656434396237|9.550179688053108e-10|True|
|B1_old_cycle_append|0.000125|7.098130532078332e-05|1.1940016144429802e-10|False|

![Tiny reaction and residual](tiny_response.png)

Source reader transition only. Real circle 1.40 -> 1.35 mm is not executed.
