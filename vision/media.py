import json
import subprocess
from pathlib import Path
import cv2


def metadata(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError("Video file does not exist.")
    cap = cv2.VideoCapture(str(path))
    try:
        if not cap.isOpened():
            raise ValueError("Cannot decode this video. Try an H.264 MP4.")
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if not 1 <= fps <= 240 or min(width, height, count) <= 0:
            raise ValueError("Video metadata is invalid or unsupported.")
        return {
            "video_id": path.name,
            "fps": fps,
            "n_frames": count,
            "width": width,
            "height": height,
            "duration": count / fps,
        }
    finally:
        cap.release()


def validate_upload(path, max_seconds=120.1):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height:format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode:
        raise ValueError("The file is not a decodable video.")
    try:
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        stream = data["streams"][0]
    except (ValueError, KeyError, IndexError):
        raise ValueError("The file has no valid video stream.") from None
    if not 0 < duration <= max_seconds:
        raise ValueError("Videos must be no longer than 2 minutes.")
    if stream["width"] * stream["height"] > 3840 * 2160 * 2:
        raise ValueError("Video resolution is too large. Export a 1080p copy.")
    return metadata(path)


class VideoWriter:
    def __init__(self, path, meta, annotate=True):
        self.annotate = annotate
        width = min(meta["width"], 1280)
        height = round(meta["height"] * width / meta["width"] / 2) * 2
        self.size = (width // 2 * 2, height)
        self.log = open(Path(path).with_suffix(".log"), "wb")
        self.process = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "bgr24",
                "-s",
                f"{self.size[0]}x{height}",
                "-r",
                str(meta["fps"]),
                "-i",
                "pipe:0",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-crf",
                "25",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(path),
            ],
            stdin=subprocess.PIPE,
            stderr=self.log,
        )

    def write(self, frame, observations, t, risk, matched):
        image = cv2.resize(frame, self.size)
        if not self.annotate:
            self.process.stdin.write(image.tobytes())
            return
        w, h = self.size
        for obs in observations:
            x1, y1, x2, y2 = [int(v * size) for v, size in zip(obs.box, [w, h, w, h])]
            color = (105, 205, 130) if obs.kind == "person" else (225, 180, 90)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                image,
                f"{obs.kind} #{obs.id} {obs.score:.2f}",
                (x1, max(15, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
                cv2.LINE_AA,
            )
        label = f"{t:.1f}s | YOLO + ByteTrack | risk {risk:.2f}"
        if not matched:
            label += " | camera mismatch: event rules off"
        cv2.rectangle(image, (0, 0), (w, 29), (30, 30, 30), -1)
        cv2.putText(
            image,
            label,
            (9, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (240, 240, 240),
            1,
            cv2.LINE_AA,
        )
        self.process.stdin.write(image.tobytes())

    def close(self, success=True):
        try:
            self.process.stdin.close()
            if not success:
                self.process.terminate()
            code = self.process.wait(timeout=40)
            if success and code:
                raise RuntimeError("Annotated video encoding failed.")
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
            raise RuntimeError("Video encoding timed out.") from None
        finally:
            self.log.close()
