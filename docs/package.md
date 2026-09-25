Submit **one link to a public Git repository** (tag or commit hash) plus **one link to your team website**. The repository must run with the two commands below on a clean machine. One submission per team; the tagged commit at the deadline is what we run, later commits are ignored.

**Repository layout**
```typescript
your-repo/
├── solution.py            # the interface from "Output format & interface"
├── run_submission.py      # from the starter kit, unchanged
├── evaluate.py            # from the starter kit, unchanged
├── requirements.txt       # or Dockerfile
├── weights/               # model weights, or download.sh that fetches them (≤ 5 GB)
├── src/                   # your code: models, tracking, rules, training scripts
├── notebooks/             # optional: EDA, experiments, training
├── predictions_samples.json  # your output on the sample videos
└── README.md
```

We run, offline, on the machine described in **Evaluation & scoring**:
```bash
pip install -r requirements.txt     # or: docker build -t team .
python run_submission.py --videos /data/test --out predictions.json
```

**README must state**

- How to install and run, including how weights are obtained (`weights/download.sh` is run once, with internet, before evaluation).
- The approach: architecture, models used, datasets used for training with licences, what is rule-based and what is learned.
- Fixed seeds and anything non-deterministic.
- Team members and who did what.

Before submitting, run `python evaluate.py --pred predictions.json --validate-only`.
