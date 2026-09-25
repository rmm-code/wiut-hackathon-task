# Camera regression fixture

`c3902.png` is the first frame of the organizer-supplied C3902.MP4, downsampled to 960 × 540 with OpenCV INTER_AREA. The original was supplied locally by the user on 24 September 2026. It reproduces rejection by the single-scale matcher and successful recognition by the native-resolution fallback. It contains no hand-labeled events and is not an accuracy evaluation set. No additional camera footage was collected.

`signal-red.png` and `signal-green.png` are aligned crops of the visible median vehicle-signal head at 10 and 40 seconds in the supplied C3896 video. They verify the configured lamp thresholds. These are inspected signal states, not accident/event ground truth.
