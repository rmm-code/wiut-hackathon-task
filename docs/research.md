# Model selection and provenance

This project uses pretrained open weights and has not trained or fine-tuned a model. Source checkpoint metrics are not our accuracy measurements.

| Component | Source | Local use and limits |
| --- | --- | --- |
| YOLO11s | [Ultralytics](https://docs.ultralytics.com/models/yolo11/) | COCO road users at approximately 7.5 sampled frames/s on C3905; ByteTrack identities are not unique-person ground truth. |
| Fire/smoke YOLO26n | [seawsurf/fire_smoke_detection_box](https://huggingface.co/seawsurf/fire_smoke_detection_box) | Checkpoint declares CC BY 4.0; author credits FASDD CV. Runs at approximately 1 Hz, requires two observations, and gates evidence to the road. Tiny/distant smoke and brief events can be missed. |
| Accident YOLO11x | [Enos-123/traffic-accident-detection-yolo11x](https://huggingface.co/Enos-123/traffic-accident-detection-yolo11x) | Author Uppada Enos; checkpoint declares MIT. Appearance boxes alone do not establish first contact. Temporal confirmation and participant stopping constrain intervals, but static wrecks and camera domain shift remain limitations. |

Exact revisions, download URLs, SHA-256 hashes, and declared licences are in `weights/manifest.json`. Ultralytics runtime/base-model terms remain applicable independently of checkpoint metadata. Source attribution must remain with redistributed weights. The three active checkpoints total 139.1 MB, below the 5 GB limit. `python -m scripts.setup` downloads and verifies them before judging; inference never calls that script.

The two source repositories' example images were downloaded into `research/model-checks/` only for functional inspection. The fire model produced fire/smoke detections on the fire example; the accident model detected the crash example. Neither produced incident detections on the two inspected organizer-camera stills. These checks are not an independent test set and establish neither recall nor precision. No extra footage from the target camera was collected.

Checkpoint loading uses PyTorch's restricted weights-only unpickler with a narrow allowlist of neural-network module classes. It does not opt into unrestricted pickle execution.

## Deployment evidence

A Linux x86_64 Docker environment successfully loaded and ran all three checkpoints on a blank frame with `--network none`; all 30 Python tests also passed in that environment. This verifies offline loading and Linux CPU compatibility, not NVIDIA performance. The installed CUDA build reports support for `sm_75`, the Turing generation used by T4. `requirements.txt` now selects the CUDA 12.6 build of torch 2.13.0 from PyTorch's index. PyPI's default Linux wheel needs CUDA 13, and therefore an NVIDIA driver of 580 or later; CUDA 12.x runs on drivers from 525 up through minor-version compatibility. The judging driver and GPU runtime are still unverified. Sources: [NVIDIA compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html), [architecture matrix](https://docs.nvidia.com/datacenter/tesla/drivers/cuda-toolkit-driver-and-architecture-matrix.html).

## Validation plan

1. All four original organizer samples have now been obtained and analyzed. Preserve their verified source files and saved outputs for reproducibility.
2. Independently annotate full clips using official class definitions and exact boundaries; save reviewer identity and uncertainty notes. The app's label panel starts empty and prevents exporting drafts as ground truth.
3. Hold out complete clips or contiguous intervals before tuning thresholds. Report macro temporal F1 at 0.3/0.5/0.7 and causal anticipation metrics using the unchanged evaluator.
4. Review both false positives and false negatives. Do not tune only on predicted events, and do not treat absence of detected accidents as evidence that accidents were absent.
5. Verify legal directions, signals and prohibited movements before enabling dependent rules. Unknown facts stay disabled.
6. Measure combined Part A + B on the intended NVIDIA machine and verify all outputs with networking disabled before release.
