# Prototype Instructions

## Project preferences

- Phase 2 is now authorized: connect real local Python inference and job processing while preserving the approved frontend design.
- Adapt the supplied references in `../design/` to traffic review; keep the neutral shell, compact cards, timeline, and table.
- Use black/charcoal for branding, primary actions, navigation, focus, and the risk chart. Keep surfaces and secondary text neutral grey, with no violet/lavender accents. Reserve restrained color for semantic traffic data.
- Dashboard order: thin page bar, summary cards, then the Video & risk panel open at the top, then the timeline, the event log and the details. Avoid large page heroes and promotional copy.
- The live demo has its own "Live demo" tab. Uploads from anywhere land there, with progress and results on that page.
- No manual-review workflow in the UI (no "To review" column or review card), no page footer and no page notes.
- The team name is Pitstop; there is no logo mark.
- The sidebar can be hidden on desktop (the button beside the name; a menu button in the top bar brings it back). It has no "Main menu" label.
- The job status bar shows only while a video uploads or is analysed, or after a failure. There is no Reanalyze button, and saved samples open without a notification.
- The Live demo page is one card: the drop area on the left and the three steps on the right, stacked on phones.
- Do not restore the sidebar promotional block or the W / WIUT Hackathon / Traffic intelligence workspace card; the user explicitly removed both.
- Use English throughout. Keep comments short and source filenames concise.
- Keep authored source files at or below 700 lines; review executable files at 500 lines.
- Opening a sample must reuse its saved analysis or attach to its current run. Starting over requires the explicit Reanalyze action. Analysis completion and manual review progress must remain distinct.
- Keep illustrative data clearly marked and separate from imported analysis.
- Default to local work; publication is not requested for Phase 1.

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.
