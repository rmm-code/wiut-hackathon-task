# Website notes

The public site at https://wiut.mardonjon.me: React + Vite in `src/`, served by nginx from
`dist/client` (`npm run build`), with the FastAPI backend in `../api`.

## Design decisions

- Neutral shell, compact cards. Black/charcoal for branding, primary actions, navigation, focus and
  the risk chart; neutral grey surfaces and secondary text; no violet or lavender. Colour only for
  traffic data.
- The team name is Pitstop, shown as text with no logo mark.
- The sidebar has no "Main menu" label, no footer text and no promotional blocks. On desktop it can
  be hidden with the button beside the name; the menu button in the top bar brings it back. The top
  bar shows only the page title.
- Dashboard order: summary cards (event overview, traffic activity), then the Video & risk panel,
  open, then the timeline, the event log, the operator summary and the analysis details.
- Class names and definitions are the task's exact wording (docs/task.md, "Event classes").
- The event timeline has one row for each of the 14 official classes, in the task's order, with its
  count. An empty row says "None found in this video", or "Switched off in our model" for a class
  the engine has off (near miss). On phones each class name sits above its track.
- Event colour means severity everywhere: red critical, amber warning, green notice, as in the
  event overview. The severity levels are ours, not the task's; the Report page says so. Every
  chart with more than one colour has a legend.
- The live demo has its own tab. It holds the drop area and the three steps in one card, stacked
  on phones. An upload shows its progress and then its results on that page.
- Only real results are shown: no illustrative or example data, no import of results files, no
  manual-review or labelling tools.
- The job status bar appears only while a video uploads or is analysed, or after a failure. Saved
  samples open without a notification, and there is no Reanalyze button.
- No page footers or page notes.

## Working rules

- English throughout; short comments; source files at most 700 lines.
- Text keeps at least 4.5:1 contrast on its own background: #737373 is the lightest grey on white;
  use #666 on tinted surfaces.
- Run the dev server and check changes in the browser before deploying.
- Record lasting design decisions from the user in this file.
