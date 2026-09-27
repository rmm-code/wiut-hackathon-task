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
- The live demo has its own tab. It holds the drop area and the three steps in one card, stacked
  on phones. An upload shows its progress and then its results on that page.
- Only real results are shown: no illustrative or example data, no import of results files, no
  manual-review or labelling tools.
- The job status bar appears only while a video uploads or is analysed, or after a failure. Saved
  samples open without a notification, and there is no Reanalyze button.
- No page footers or page notes.

## Working rules

- English throughout; short comments; source files at most 700 lines.
- Run the dev server and check changes in the browser before deploying.
- Record lasting design decisions from the user in this file.
