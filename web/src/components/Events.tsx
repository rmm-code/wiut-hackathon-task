import { Fragment, useEffect, useMemo, useState } from "react";
import { CardHead, Empty } from "./Card";
import { Icon } from "./Icon";
import { classes } from "../data/classes";
import { time } from "../lib/format";
import type { Analysis, TrafficEvent } from "../types";

export function Events({
  analysis,
  selected,
  onSelect,
  onExport,
}: {
  analysis: Analysis;
  selected: string | null;
  onSelect: (event: TrafficEvent) => void;
  onExport: () => void;
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(0);
  useEffect(() => {
    if (!selected) return;
    const index = [...analysis.events]
      .sort((a, b) => a.start - b.start)
      .findIndex((event) => event.id === selected);
    setQuery("");
    setFilter("all");
    setSort("asc");
    setPage(Math.max(0, Math.floor(index / 5)));
  }, [selected]);
  const filtered = useMemo(
    () =>
      analysis.events
        .filter((event) => {
          const text =
            `${event.id} ${classes[event.label].name} ${event.lane ?? ""}`.toLowerCase();
          return (
            text.includes(query.toLowerCase()) &&
            (filter === "all" || classes[event.label].level === filter)
          );
        })
        .sort((a, b) =>
          sort === "asc" ? a.start - b.start : b.start - a.start,
        ),
    [analysis.events, query, filter, sort],
  );
  const current = Math.min(
    page,
    Math.max(0, Math.ceil(filtered.length / 5) - 1),
  );
  const visible = filtered.slice(current * 5, current * 5 + 5);
  return (
    <section className="card events-card" id="events">
      <CardHead
        icon="menu"
        title="Event log"
        subtitle="Every detected event. Click one to jump the video to it."
        action={
          <button
            className="button small"
            disabled={analysis.origin === "none"}
            onClick={onExport}
          >
            <Icon name="download" size={15} />
            Export JSON
          </button>
        }
      />
      <div className="table-tools">
        <div className="table-tabs">
          <button
            className={filter === "all" ? "active" : ""}
            onClick={() => {
              setFilter("all");
              setPage(0);
            }}
          >
            All events <span>{analysis.events.length}</span>
          </button>
        </div>
        <div className="table-filters">
          <label className="search-field">
            <Icon name="search" size={16} />
            <input
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(0);
              }}
              placeholder="Search events…"
              aria-label="Search events"
            />
          </label>
          <label className="select-field">
            <Icon name="filter" size={15} />
            <select
              aria-label="Filter events by severity"
              value={
                ["critical", "warning", "notice"].includes(filter)
                  ? filter
                  : "all"
              }
              onChange={(e) => {
                setFilter(e.target.value);
                setPage(0);
              }}
            >
              <option value="all">Severity</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="notice">Notice</option>
            </select>
          </label>
        </div>
      </div>
      {!visible.length ? (
        <Empty
          title={
            analysis.origin === "none" ? "No analysis yet" : "No events to show"
          }
          text={
            analysis.origin === "none"
              ? "Open a local video and import its results, or explore the preview."
              : "Try a different search or filter."
          }
          icon="search"
        />
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Event</th>
                <th>
                  <button
                    onClick={() => setSort(sort === "asc" ? "desc" : "asc")}
                  >
                    Time{" "}
                    <Icon name={sort === "asc" ? "down" : "right"} size={13} />
                  </button>
                </th>
                <th>Location</th>
                <th>Confidence</th>
                <th>
                  <span className="sr-only">Details</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {visible.map((event) => (
                <Fragment key={event.id}>
                  <tr className={selected === event.id ? "selected-row" : ""}>
                    <td>
                      <button
                        className="event-name"
                        onClick={() => onSelect(event)}
                        aria-expanded={selected === event.id}
                      >
                        <span
                          className={`event-icon tone-${classes[event.label].color}`}
                        >
                          <Icon
                            name={
                              event.label.includes("light") ||
                              event.label === "stop_line"
                                ? "signal"
                                : event.label === "jaywalking"
                                  ? "person"
                                  : classes[event.label].level === "critical"
                                    ? "warning"
                                    : "car"
                            }
                            size={17}
                          />
                        </span>
                        <span>
                          {classes[event.label].name}
                          <small>{event.id}</small>
                        </span>
                      </button>
                    </td>
                    <td>
                      <span className="time-code">
                        {time(event.start)} — {time(event.end)}
                      </span>
                      <small>
                        {(event.end - event.start).toFixed(1)} seconds
                      </small>
                    </td>
                    <td>{event.lane ?? "—"}</td>
                    <td>
                      {event.confidence === undefined ? (
                        <span className="muted">—</span>
                      ) : (
                        <div className="confidence">
                          <span
                            className="confidence-ring"
                            style={{
                              borderColor:
                                event.confidence >= 0.9 ? "#78b99b" : "#d8b570",
                            }}
                          />
                          {Math.round(event.confidence * 100)}%
                        </div>
                      )}
                    </td>
                    <td>
                      <button
                        className="icon-button"
                        onClick={() => onSelect(event)}
                        aria-label={`View ${event.id} details`}
                      >
                        <Icon name="external" size={17} />
                      </button>
                    </td>
                  </tr>
                  {selected === event.id && (
                    <tr className="event-detail">
                      <td colSpan={5}>
                        <span
                          className={`badge badge-${classes[event.label].color}`}
                        >
                          {classes[event.label].level}
                        </span>
                        <p>{classes[event.label].description}</p>
                        <span>
                          {analysis.origin === "preview"
                            ? "Illustrative event. This is not a finding from the source video."
                            : analysis.origin === "model"
                              ? "Found by the model in this video."
                              : "Imported from a results file."}
                        </span>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="table-footer">
        <span>
          {filtered.length
            ? `${current * 5 + 1}–${Math.min((current + 1) * 5, filtered.length)} of ${filtered.length} events`
            : "0 events"}
        </span>
        <div>
          <button
            className="button small"
            disabled={current === 0}
            onClick={() => setPage(current - 1)}
          >
            <Icon name="left" size={14} />
            Previous
          </button>
          <span>
            {current + 1} / {Math.max(1, Math.ceil(filtered.length / 5))}
          </span>
          <button
            className="button small"
            disabled={(current + 1) * 5 >= filtered.length}
            onClick={() => setPage(current + 1)}
          >
            Next
            <Icon name="right" size={14} />
          </button>
        </div>
      </div>
    </section>
  );
}
