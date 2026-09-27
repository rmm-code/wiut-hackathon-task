export const labels = [
  "accident",
  "near_miss",
  "red_light",
  "wrong_way",
  "illegal_u_turn",
  "stopped_vehicle",
  "jaywalking",
  "failure_to_yield",
  "illegal_turn",
  "solid_line_crossing",
  "stop_line",
  "congestion",
  "road_obstacle",
  "fire_smoke",
] as const;

export type Label = (typeof labels)[number];
export type Page = "dashboard" | "demo" | "samples" | "report" | "team";
export type Level = "critical" | "warning" | "notice";
export type EventTuple = [number, number, Label];
export type RiskPoint = [number, number];

export interface TrafficEvent {
  id: string;
  label: Label;
  start: number;
  end: number;
  confidence?: number;
  lane?: string;
}

export interface Video {
  id: string;
  name: string;
  duration: number;
  condition: string;
  source: "sample" | "local";
  url?: string;
  link?: string;
}

export interface Analysis {
  origin: "model" | "none";
  events: TrafficEvent[];
  risk: RiskPoint[];
  report?: EngineReport;
}

export interface Activity {
  time: string;
  cars: number;
  buses: number;
  people: number;
}

export interface EngineReport {
  eda?: {
    counts: { time: number; objects: Record<string, number>; total: number }[];
    units: Record<string, string>;
  };
  meta: {
    duration: number;
    fps: number;
    width: number;
    height: number;
    decoded_frames: number;
    sample_fps: number;
  };
  engine: {
    model: string;
    device: string;
    tracker: string;
    synthetic: boolean;
  };
  scene: { id: string; matched: boolean; calibration: string; inliers: number };
  coverage: {
    label: Label;
    enabled: boolean;
    status: string;
    reason: string;
  }[];
  summary: {
    road_users: number;
    by_class: Record<string, number>;
    activity: Activity[];
    runtime_sec: number;
    brightness_mean: number;
  };
  details: {
    label: Label;
    start: number;
    end: number;
    confidence: number;
    lane?: string;
    evidence: string;
  }[];
  limitations: string[];
}

export interface Job {
  id: string;
  state:
    | "loading"
    | "uploading"
    | "queued"
    | "running"
    | "complete"
    | "failed"
    | "cancelled";
  progress: number;
  stage: string;
  processed_frames?: number;
  total_frames?: number;
  error?: string;
  detail?: string;
  elapsed_sec?: number;
}

export interface JobResult extends PredictionFile {
  sample_id?: string | null;
  analysis: EngineReport;
  video_url: string;
}

export interface PredictionFile {
  team?: string;
  videos: Record<string, { events: EventTuple[]; risk?: RiskPoint[] }>;
}

// The future API adapter resolves this contract; pages never call the model.
export interface AnalysisService {
  submit(file: File): Promise<{ id: string }>;
  status(id: string): Promise<{
    state: "queued" | "running" | "complete" | "failed";
    progress: number;
  }>;
  result(id: string): Promise<PredictionFile>;
}

export interface ProjectInfo {
  team: {
    name: string;
    role: string;
    contribution: string;
    links: Record<string, string>;
    photo?: string;
    projects?: { name: string; description: string; url: string }[];
  }[];
  models: {
    name: string;
    purpose: string;
    method: string;
    dataset: string;
    dataset_url: string;
    dataset_license: string;
    model_license: string;
    source: string;
    download: string;
    sha256: string;
  }[];
  samples: {
    id: string;
    name: string;
    frames: number;
    duration: number;
    fps: number;
    width: number;
    height: number;
    by_class: Record<string, number>;
    events: number;
    road_users: number;
    runtime: number;
    brightness: number;
  }[];
  coverage: EngineReport["coverage"];
  repository: string;
  predictions: string;
  manifest: string;
  devset: DevsetReport | null;
  ablation: AblationReport | null;
  confusion: ConfusionReport | null;
  release: {
    tag: string | null;
    weights_url: string | null;
    samples_url: string | null;
  };
}

export interface ConfusionReport {
  threshold: number;
  rows: Partial<Record<Label, Record<string, number>>>;
  missed: Partial<Record<Label, number>>;
}

export interface AblationReport {
  labels: string;
  rows: {
    variant: string;
    score_a: number;
    events: number;
    per_class: Partial<Record<Label, number>>;
  }[];
}

export interface DevsetReport {
  score_a: number;
  videos: string[];
  labelled_events: number;
  note: string;
  classes: {
    label: Label;
    labelled: number;
    predicted: number;
    precision: number;
    recall: number;
    "f1_0.3": number;
    "f1_0.5": number;
    "f1_0.7": number;
    f1_mean: number;
  }[];
}
