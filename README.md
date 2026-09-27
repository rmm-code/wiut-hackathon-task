# Pitstop: WIUT Hackathon CV Track

Finds traffic violations in video from one fixed road camera (Part A), and gives, for every frame,
a score for how likely an accident is to start within 5 seconds (Part B).

- Website and live demo: https://wiut.mardonjon.me
- Release with weights and sample results: [v1.0.0](https://github.com/rmm-code/wiut-hackathon-task/releases/tag/v1.0.0)
- One-page report: [docs/report.md](docs/report.md)

## Run

Needs Python 3.10–3.13 (on Linux, OpenCV also needs `libgl1` and `libglib2.0-0`) and, for the GPU,
an NVIDIA driver 525 or newer (a T4 works).
Download the weights once, with internet; the run itself is offline.

```sh
pip install -r requirements.txt
sh weights/download.sh             # 3 checkpoints, 139 MB, SHA-256 checked
python run_submission.py --videos /data/test --out predictions.json
python evaluate.py --pred predictions.json --validate-only
```

- `run_submission.py` and `evaluate.py` are the organizers' files, unchanged (a test checks their hashes).
- Instead of the download script you can extract `weights.tar` from the release in the repository root.
- Docker: `docker build -t pitstop .` downloads the weights during the build. Run it with
  `docker run --rm --gpus all --network none -v /data/test:/data/test:ro -v "$PWD/output:/results" pitstop python run_submission.py --videos /data/test --out /results/predictions.json`.
  Without `--gpus all` it runs on the CPU, which is too slow for the time limit.

## How it works

1. **Detect (learned).** A pretrained YOLO11s finds cars, buses, trucks, motorcycles, bicycles and
   people in every 4th frame, about 7.5 frames per second.
2. **Track (rule-based).** ByteTrack joins the detections into tracks.
3. **Align (rule-based).** SIFT and RANSAC match the video to the reference view of the camera. If the
   first frame fails, one frame per second of the first 20 seconds is tried. If none matches, the
   video is treated as another camera and the scene rules are switched off.
4. **Scene rules (rule-based).** The lanes, stop line, solid lines, crossings and signal were mapped once
   for this camera ([config/camera.json](config/camera.json), [docs/calibration.md](docs/calibration.md)).
   Each class is a small rule over the tracks and this map ([docs/classes.md](docs/classes.md)).
5. **Specialists (learned).** Two open YOLO models look for accidents and fire or smoke once a second.
   The tracks must confirm them.
6. **Segments (rule-based).** Short blips are dropped and fragments of the same class are merged.
7. **Part B risk (rule-based).** A separate `RiskEstimator` runs its own detector and tracker on the frames
   it is given, and scores how close tracked road users come to colliding. It never reads the video
   file or Part A's output.

13 of the 14 classes are on. `near_miss` is off: every near-miss detection on the samples was a false
alarm, and a predicted class that is absent from the test set scores 0.

## Results on our own labels

There are no official labels for the samples, so we labelled the four sample videos ourselves
([devset/](devset/README.md)). Score it with
`python evaluate.py --pred predictions_samples.json --gt devset/labels.json`.

| Class | Labelled | Predicted | Precision | Recall | F1 at IoU 0.3 / 0.5 / 0.7 |
| --- | ---: | ---: | ---: | ---: | --- |
| stop_line | 10 | 10 | 1.00 | 1.00 | 1.00 / 1.00 / 1.00 |
| red_light | 3 | 3 | 1.00 | 1.00 | 1.00 / 1.00 / 1.00 |
| illegal_turn | 5 | 4 | 1.00 | 0.80 | 0.89 / 0.89 / 0.67 |
| solid_line_crossing | 2 | 3 | 0.67 | 1.00 | 0.80 / 0.80 / 0.40 |
| failure_to_yield | 22 | 33 | 0.52 | 0.77 | 0.62 / 0.62 / 0.58 |
| jaywalking | 36 | 36 | 0.61 | 0.61 | 0.72 / 0.61 / 0.39 |

Score A on these labels is **0.777**. The rules were tuned on the same videos, so expect less on the
hidden test set. Accident, fire and smoke, road obstacle, congestion, wrong way and illegal U-turn
never happen in the samples, so their accuracy is unknown. Part B cannot be measured on the samples
either, since they contain no accident.

## Runtime

The limit is 3 × the video length for Part A and Part B together. On sample C3905 (128 s, limit 383 s):

| Machine | Time | Share of the limit |
| --- | ---: | ---: |
| Apple M5 | 97 s | 25% |
| RTX 4060 with an Intel i5-12400 | 135 s | 35% |
| The same PC limited to 2 CPU cores | 235 s | 61% |
| Tesla T4 with 2 slow CPU cores (Google Colab) | 412 s | over the limit |

Decoding the 4K video, not the GPU, sets the speed. Part A decodes on a background thread while it
analyses. If a slow machine would still run over the limit, Part B stops early
([vision/budget.py](vision/budget.py)), so the video keeps its events and loses only its risk curve.
Part A has no such guard: on Colab's 2 CPU cores it alone took 412 s, so that video scored empty.
The organizers' machine has 8 cores. The same Colab T4 ran a 20-second clip within its limit, with
the same events as on the Mac.

## Reproducibility

- Seeds are fixed at 42 (Python, NumPy, Torch, OpenCV). cuDNN benchmarking is off and deterministic
  cuDNN is requested.
- Running the tagged code on the samples reproduces the events and risk curves in
  `predictions_samples.json` exactly.
- CPU, Apple and NVIDIA GPUs can differ slightly in floating point. On the RTX 4060 a few event
  boundaries moved, with the same score on our labels.
- The Part B time guard reads the clock, so on a machine close to the limit two runs can differ in
  their risk curves. Events are not affected.
- No model was trained. The numbers above come from `python -m scripts.devset score`,
  `python -m scripts.ablation` and `python -m scripts.confusion`. Tests: `python -m pytest -q tests`.

## Models, datasets and licences

| Model | Trained on | Data licence | Model licence |
| --- | --- | --- | --- |
| YOLO11s, Ultralytics | COCO 2017 | [COCO terms](https://cocodataset.org/#termsofuse): annotations CC BY 4.0, images keep their Flickr terms | AGPL-3.0 |
| Fire/smoke YOLO26n, [seawsurf](https://huggingface.co/seawsurf/fire_smoke_detection_box) | [FASDD CV](https://huggingface.co/datasets/seawsurf/fire_smoke_dataset_fasdd_cv) | CC BY 4.0 (publisher) | CC BY 4.0 (publisher); Ultralytics terms apply |
| Accident YOLO11x, [Uppada Enos](https://huggingface.co/Enos-123/traffic-accident-detection-yolo11x) | [Traffic Accident Detection, hilmantm](https://universe.roboflow.com/hilmantm/traffic-accident-detection) | CC BY 4.0 (publisher) | MIT (publisher); Ultralytics terms apply |

The organizers' four sample videos were used for the camera map, our labels and tests, not for
training. Checkpoint versions and hashes are pinned in `weights/manifest.json`. ByteTrack runs
through Ultralytics. No hosted or paid model is called at any point.

## Repository

```text
solution.py           the competition interface (Part A and Part B)
vision/               detection, tracking, alignment, rules, segments, risk, rendering
config/camera.json    the camera map, with the evidence for each fact
devset/               our labels of the samples and their scores
api/, web/            the website's server and pages
scripts/              weight download, dev-set tools, packaging
tests/                tests
docs/                 report, classes, calibration, architecture, submission checklist
```

To run the website locally: `npm --prefix web ci && npm run dev` (needs Node 22.18+ and the Python
setup above).

## Team Pitstop

| Member | Role | Did | Previous projects | Links |
| --- | --- | --- | --- | --- |
| Mardonjon Rasulov | Captain | The design and most of the logic: detection pipeline, traffic rules, risk score, website | [Sifatly](https://sifatly.com) (food and product scanner, about 10,000 users, $250 MRR), [Tarjimonchi](https://tarjimonchi.uz) (AI translation of Word documents) | [Portfolio](https://mardonjon.me), [GitHub](https://github.com/rmm-code), [LinkedIn](https://www.linkedin.com/in/mardonjon-rasulov-6012762b7), [Instagram](https://www.instagram.com/mardonjon_rasulov/) |
| Saidxon Xaydarov | Member | Tested the system, helped with the website's UX | [Fikrly](https://fikrly.uz) (reviews of businesses in Uzbekistan) | [Portfolio](https://xaydarov.uz), [GitHub](https://github.com/khdrvss), [LinkedIn](https://www.linkedin.com/in/saidxon-xaydarov), [Instagram](https://www.instagram.com/saidxon_xaydarov/) |
| Miraziz Mirvaliyev | Member | Built parts of the logic, tested it | [Driver Management](https://github.com/MMiraziz013/Driver_Management_Frontend), [HR Service](https://github.com/MMiraziz013/HR_Service) | [GitHub](https://github.com/MMiraziz013), [LinkedIn](https://www.linkedin.com/in/miraziz-mirvaliyev-75a685236/) |
