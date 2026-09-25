import argparse
from pathlib import Path
from .pipeline import analyze, write_json


def main():
    parser = argparse.ArgumentParser(description="Run local traffic analysis.")
    parser.add_argument("video")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    def progress(**data):
        write_json(out / "progress.json", data)

    result = analyze(args.video, output=out, progress=progress, time_limit=1800)
    write_json(
        out / "predictions.json",
        {
            "team": "wiut",
            "videos": {
                Path(args.video).name: {
                    "events": result["events"],
                    "risk": result["risk"],
                }
            },
        },
    )
    print(
        f"{len(result['events'])} events; {result['summary']['road_users']} tracked road users; {result['summary']['runtime_sec']} seconds"
    )


if __name__ == "__main__":
    main()
