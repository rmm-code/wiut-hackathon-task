import { useEffect, useRef, useState } from "react";
import { samples } from "../data/samples";
import { openVideo } from "../lib/media";
import { parseResults } from "../lib/results";
import { download } from "../lib/format";
import { useJob } from "./useJob";
import type { Analysis, Page, TrafficEvent, Video } from "../types";

function currentPage(): Page {
  const route = window.location.hash.replace("#/", "");
  return ["dashboard", "demo", "samples", "report", "team"].includes(route)
    ? (route as Page)
    : "dashboard";
}

const empty: Analysis = { origin: "none", events: [], risk: [] };

export function useWorkspace() {
  const [page, setPage] = useState<Page>(currentPage);
  const [video, setVideo] = useState<Video>(samples[0]);
  const [analysis, setAnalysis] = useState<Analysis>(empty);
  const [position, setPosition] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const player = useRef<HTMLVideoElement>(null);
  const uploadRequest = useRef(0);
  const jobs = useJob((result) => {
    const name = Object.keys(result.videos)[0];
    const parsed = parseResults(result, name, result.analysis.meta.duration);
    const events = parsed.events.map((event) => {
      const detail = result.analysis.details.find(
        (item) =>
          item.label === event.label &&
          Math.abs(item.start - event.start) < 0.01,
      );
      return {
        ...event,
        confidence: detail?.confidence,
        lane: detail?.lane ?? undefined,
      };
    });
    setAnalysis({
      ...parsed,
      events,
      origin: "model",
      report: result.analysis,
    });
    const sample = samples.find(item => item.id === result.sample_id);
    setVideo({
      ...(sample ?? { id: `analysis-${name}`, name, source: "local" as const, condition: "Analyzed video" }),
      url: result.video_url,
      duration: result.analysis.meta.duration,
    });
    setPosition(0);
    setPlaying(false);
    // Saved samples open silently; an upload announces that its analysis finished.
    if (!sample)
      setToast(
        `Analysis complete: ${events.length} events and ${result.analysis.summary.road_users} tracked road users.`,
      );
  });

  useEffect(() => {
    const change = () => {
      setPage(currentPage());
      setPlaying(false);
    };
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);

  useEffect(
    () => () => {
      if (video.url) URL.revokeObjectURL(video.url);
    },
    [video.url],
  );
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 4500);
    return () => clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    if (video.url || !playing) return;
    const timer = setInterval(
      () =>
        setPosition((value) => {
          if (value + 0.25 >= video.duration) {
            setPlaying(false);
            return video.duration;
          }
          return value + 0.25;
        }),
      250,
    );
    return () => clearInterval(timer);
  }, [playing, video.url, video.duration]);

  useEffect(() => {
    if (!player.current || !video.url) return;
    if (playing)
      player.current.play().catch(() => {
        setPlaying(false);
        setToast("Playback could not start. Try the video controls again.");
      });
    else player.current.pause();
  }, [playing, video.url]);

  function navigate(next: Page) {
    window.location.hash = `/${next}`;
    setPage(next);
    if (next !== "dashboard" && next !== "demo") setPlaying(false);
  }

  function choose(next: Video, page: Page = "dashboard") {
    if (video.id === next.id && jobs.job && jobs.job.state !== "failed" && jobs.job.state !== "cancelled") {
      navigate(page);
      return;
    }
    jobs.reset();
    uploadRequest.current++;
    setVideo(next);
    setAnalysis(empty);
    setPosition(0);
    setSelected(null);
    setPlaying(false);
    navigate(page);
    if (next.source === "sample")
      void jobs
        .start(next.id)
        .catch((error) =>
          setToast(
            error instanceof Error
              ? error.message
              : "Could not open the sample.",
          ),
        );
  }

  async function upload(file: File) {
    const request = ++uploadRequest.current;
    const media = await openVideo(file);
    if (request !== uploadRequest.current) {
      URL.revokeObjectURL(media.url);
      return;
    }
    choose({
      id: `local-${Date.now()}`,
      name: file.name,
      ...media,
      source: "local",
      condition: "Local video",
    }, "demo");
    await jobs.start(file);
    setToast("Video sent to the local analysis server.");
  }

  function seek(value: number) {
    const next = Math.max(0, Math.min(value, video.duration));
    setPosition(next);
    if (player.current) player.current.currentTime = next;
  }

  function pick(event: TrafficEvent) {
    setSelected(event.id);
    seek(event.start);
    setPlaying(false);
  }

  function exportResults() {
    download("predictions.json", {
      team: "pitstop",
      videos: {
        [video.name]: {
          events: analysis.events.map((e) => [e.start, e.end, e.label]),
          risk: analysis.risk,
        },
      },
    });
    setToast("Results exported as JSON.");
  }

  return {
    job: jobs.job,
    cancelJob: () => { void jobs.cancel().catch(error => setToast(error.message)); },
    page,
    video,
    analysis,
    position,
    playing,
    selected,
    toast,
    player,
    navigate,
    choose,
    upload,
    seek,
    pick,
    exportResults,
    setPlaying,
    setPosition,
    setToast,
    setSelected,
  };
}

export type Workspace = ReturnType<typeof useWorkspace>;
