import { useEffect, useRef, useState } from "react";
import { CardHead } from "./Card";
import { Icon } from "./Icon";
import { time } from "../lib/format";
import type { Workspace } from "../hooks/useWorkspace";

export function Camera({ workspace: w }: { workspace: Workspace }) {
  const container = useRef<HTMLElement>(null);
  const [fullscreen, setFullscreen] = useState(false);
  useEffect(() => {
    const update = () => setFullscreen(document.fullscreenElement === container.current);
    document.addEventListener("fullscreenchange", update);
    return () => document.removeEventListener("fullscreenchange", update);
  }, []);
  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement === container.current) await document.exitFullscreen();
      else await container.current?.requestFullscreen();
    } catch {
      w.setToast("Fullscreen is unavailable in this browser. Open the video in a new tab to enlarge it.");
    }
  }
  const still = !w.video.url;
  const canPlay =
    Boolean(w.video.url) ||
    w.video.source === "demo" ||
    w.analysis.origin === "imported";
  function toggle() {
    if (w.position >= w.video.duration) w.seek(0);
    w.setPlaying(!w.playing);
  }
  return (
    <section ref={container} className="card camera-card">
      <CardHead
        icon="camera"
        title={
          w.video.source === "local" ? "Video workspace" : "Intersection 01"
        }
        subtitle={
          w.video.source === "demo"
            ? "Tashkent · fixed road camera"
            : w.video.name
        }
        action={
          <span className="badge badge-neutral">
            <Icon name={still ? "eye" : "film"} size={13} />
            {still
              ? "Reference still"
              : w.analysis.origin === "model"
                ? "YOLO annotations"
                : "Local playback"}
          </span>
        }
      />
      <div className="camera-visual">
        {still ? (
          <img
            src="/images/camera.webp"
            alt="The supplied Tashkent intersection with marked crossings, traffic lights, vehicles, and pedestrians."
          />
        ) : (
          <video
            key={w.video.url}
            ref={w.player}
            src={w.video.url}
            playsInline
            onLoadedMetadata={() => w.seek(w.position)}
            onTimeUpdate={(event) =>
              w.setPosition(event.currentTarget.currentTime)
            }
            onEnded={() => w.setPlaying(false)}
            onError={() =>
              w.setToast("Playback failed. Try an H.264 MP4 video.")
            }
          />
        )}
        <div className="camera-top">
          <span>
            <Icon name="camera" size={14} />
            {still ? "CAM 01" : "LOCAL VIDEO"}
          </span>
          <span>{still ? "SOURCE CAMERA" : "ON THIS DEVICE"}</span>
        </div>
        {still && (
          <span className="still-note">
            {w.video.source === "demo"
              ? "Camera reference · timeline uses example events"
              : "Shared camera reference · original video linked below"}
          </span>
        )}
      </div>
      <div className="playback-controls">
        <button
          className="play-button"
          disabled={!canPlay}
          onClick={toggle}
          aria-label={
            w.playing
              ? "Pause playback"
              : still
                ? "Play preview timeline"
                : "Play video"
          }
        >
          <Icon name={w.playing ? "pause" : "play"} size={17} weight="fill" />
        </button>
        <span className="time-code">
          {time(w.position)} <span>/ {time(w.video.duration)}</span>
        </span>
        <input
          type="range"
          min="0"
          max={w.video.duration}
          step="0.1"
          value={w.position}
          onChange={(e) => w.seek(Number(e.target.value))}
          aria-label="Playback position"
        />
        {!still && (
          <button
            className="icon-button"
            onClick={() => void toggleFullscreen()}
            aria-label={fullscreen ? "Exit fullscreen" : "Enter fullscreen"}
            title={fullscreen ? "Exit fullscreen (Esc)" : "Fullscreen"}
          >
            <Icon name={fullscreen ? "collapse" : "expand"} size={19} />
          </button>
        )}
        {w.video.link ? (
          <a
            className="icon-button"
            href={w.video.link}
            target="_blank"
            rel="noreferrer"
            aria-label="Open original sample video"
          >
            <Icon name="open" size={18} />
          </a>
        ) : (
          <button
            className="icon-button"
            onClick={() => w.seek(0)}
            aria-label="Restart timeline"
          >
            <Icon name="reset" size={18} />
          </button>
        )}
      </div>
    </section>
  );
}
