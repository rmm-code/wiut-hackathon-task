import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import type { IconName } from "./Icon";
import type { Page, Video } from "../types";
import { time } from "../lib/format";
import { samples } from "../data/samples";

export const nav: { id: Page; label: string; icon: IconName }[] = [
  { id: "dashboard", label: "Dashboard", icon: "home" },
  { id: "demo", label: "Live demo", icon: "upload" },
  { id: "samples", label: "Samples & insights", icon: "film" },
  { id: "report", label: "Approach & report", icon: "book" },
  { id: "team", label: "Our team", icon: "team" },
];

export function Sidebar({
  page,
  navigate,
  videoId,
  onSample,
  open,
  onClose,
}: {
  page: Page;
  navigate: (page: Page) => void;
  videoId: string;
  onSample: (video: Video) => void;
  open: boolean;
  onClose: () => void;
}) {
  const [mobile, setMobile] = useState(
    () => matchMedia("(max-width: 800px)").matches,
  );
  const sidebar = useRef<HTMLElement>(null);
  useEffect(() => {
    const query = matchMedia("(max-width: 800px)");
    const change = () => setMobile(query.matches);
    query.addEventListener("change", change);
    return () => query.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    if (!open || !mobile) return;
    const previous = document.activeElement as HTMLElement | null;
    const container = sidebar.current;
    container?.querySelector<HTMLAnchorElement>("a")?.focus();
    const handle = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key !== "Tab" || !container) return;
      const items = Array.from(
        container.querySelectorAll<HTMLElement>("a, button:not(:disabled)"),
      );
      const first = items[0],
        last = items.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", handle);
    return () => {
      document.removeEventListener("keydown", handle);
      previous?.focus();
    };
  }, [open, mobile]);
  return (
    <>
      {open && (
        <button
          className="nav-scrim"
          onClick={onClose}
          aria-label="Close navigation"
        />
      )}
      <aside
        ref={sidebar}
        inert={mobile && !open}
        className={`sidebar ${open ? "is-open" : ""}`}
      >
        {mobile && open && (
          <button
            className="icon-button nav-close"
            onClick={onClose}
            aria-label="Close navigation menu"
          >
            <Icon name="close" />
          </button>
        )}
        <a className="brand" href="#/dashboard" onClick={onClose}>
          Pitstop
        </a>
        <p className="nav-label">Main menu</p>
        <nav aria-label="Main navigation">
          {nav.map((item) => (
            <a
              key={item.id}
              href={`#/${item.id}`}
              className={`nav-link ${page === item.id ? "active" : ""}`}
              aria-current={page === item.id ? "page" : undefined}
              onClick={() => {
                navigate(item.id);
                onClose();
              }}
            >
              <Icon
                name={item.icon}
                size={19}
                weight={page === item.id ? "fill" : "regular"}
              />
              {item.label}
            </a>
          ))}
        </nav>
        <div className="nav-section-heading">
          <p className="nav-label">Sample videos</p>
          <span className="count-badge">04</span>
        </div>
        <div className="sample-nav">
          {samples.map((sample, i) => (
            <button
              key={sample.id}
              className={`sample-link ${sample.id === videoId ? "selected" : ""}`}
              onClick={() => {
                onSample(sample);
                onClose();
              }}
            >
              <span className={`sample-icon sample-${i}`}>
                <Icon name="camera" size={17} weight="fill" />
              </span>
              <span>{sample.name.replace(".MP4", "")}</span>
              <span className="sample-duration">{time(sample.duration)}</span>
              <Icon name="right" size={14} />
            </button>
          ))}
        </div>
        <div className="sidebar-bottom">
          <a
            className="repo-link"
            href="https://github.com/rmm-code/wiut-hackathon-task"
            target="_blank"
            rel="noreferrer"
          >
            <Icon name="github" size={20} />
            <span>
              WIUT CV Track<small>Project repository</small>
            </span>
            <Icon name="external" size={15} />
          </a>
          <div className="sidebar-footnote">© 2026 Team Pitstop</div>
        </div>
      </aside>
    </>
  );
}
