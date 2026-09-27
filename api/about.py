import json
from .samples import SAMPLE_IDS
from vision.coverage import coverage
from types import SimpleNamespace


def devset(root, name="report.json"):
    path = root / "devset" / name
    return json.loads(path.read_text()) if path.is_file() else None


def register_about(app, root, gallery):
    @app.get("/api/about")
    def about():
        config = json.loads((root / "config/camera.json").read_text())
        specialists = {
            label
            for item in config.get("specialists", [])
            if item.get("enabled")
            for label in item["classes"].values()
        }
        models = json.loads((root / "config/models.json").read_text())
        weights = json.loads((root / "weights/manifest.json").read_text())["models"]
        for model in models:
            source = next(item for item in weights if item["file"] == model["file"])
            model.update(download=source["url"], sha256=source["sha256"])
        summary = []
        for identity, name in SAMPLE_IDS.items():
            if not gallery.available(identity):
                continue
            data = gallery.analysis(identity)
            summary.append(
                {
                    "id": identity,
                    "name": name,
                    "frames": data["meta"]["decoded_frames"],
                    "duration": data["meta"]["duration"],
                    "fps": data["meta"]["fps"],
                    "width": data["meta"]["width"],
                    "height": data["meta"]["height"],
                    "by_class": data["summary"]["by_class"],
                    "events": len(data["events"]),
                    "road_users": data["summary"]["road_users"],
                    "runtime": data["summary"]["runtime_sec"],
                    "brightness": data["summary"]["brightness_mean"],
                }
            )
        return {
            "team": json.loads((root / "config/team.json").read_text()),
            "models": models,
            "samples": summary,
            "coverage": coverage(
                SimpleNamespace(config=config, matched=True),
                ["car", "person", "dog"],
                specialists,
            ),
            "repository": "https://github.com/rmm-code/wiut-hackathon-task",
            "predictions": "/api/downloads/predictions.json",
            "manifest": "/api/downloads/weights.json",
            "devset": devset(root),
            "ablation": devset(root, "ablation.json"),
            "release": json.loads((root / "config/release.json").read_text()),
        }
