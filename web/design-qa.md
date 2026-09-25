# Design QA — Phase 1

**final result: passed**

## Phase 2 integration check

The approved compact black/grey layout is preserved. New progress and analysis-details panels use the existing card, text, and status styles. Actual model output is distinguished from the retained illustrative preview.

Verified a real local MP4 upload through the browser and Python worker, then a full organizer sample. The full-sample page displayed 22 provisional candidates, 493 tracked road-user IDs, actual runtime, annotated playback, and per-frame risk. After fixing the sample playback availability condition, the annotated video played past 45 seconds and paused correctly. Screenshot evidence: `../design/qa/phase2-playback.png` at 1440 × 1050, DPR 1. The screenshot was opened and reviewed; boxes and IDs are actual YOLO/ByteTrack output. Browser console check returned no errors.

The earlier Phase 1 statements about no backend are historical. Current rule accuracy remains unvalidated, with four provisional categories active and other classes explicitly disabled. The backend/contract tests and official format check are engineering evidence, not accuracy evidence. See `../docs/report.md` for the actual benchmark and limitations.

## Latest revision — compact reference layout and sidebar removals

The user's close-up references are saved as `../design/sidebar.png` (470 × 1032) and `../design/content.png` (723 × 1150). Both the sidebar promotional card and W / WIUT Hackathon / Traffic intelligence workspace card have been removed from the component, not merely hidden. Navigation uses a restrained filled home icon, a white inset active row, section dividers, and single-line sample entries.

The latest dashboard follows the source hierarchy: thin page bar → three summary cards → timeline → event table. Large page headings, repeated subtitles, and the full-width preview banner are replaced with compact contextual labels. Preview events remain explicitly labeled as illustrative. Video and risk sit in a native disclosure below the table; selecting an event opens it and seeks playback. The report/team introductions are compact, plain descriptions rather than promotional heroes.

Latest visual evidence: `../design/qa/compact.png` and `compact-report.png`, 1440 × 1050 CSS/pixels, DPR 1. `compact-comparison.jpg` places both new reference crops alongside the rendered dashboard; it was opened and reviewed for sidebar anatomy, hierarchy, spacing, typography, colors, and source imagery. The source crops are magnified portions of a desktop reference, so comparison preserves aspect ratios rather than claiming pixel-identical viewport dimensions. The latest comparison has no actionable P0/P1/P2 findings. Event selection was verified to reveal risk and set playback to 62 seconds. Build, strict type checks, and the 700-line limit pass. The previous neutral revision and initial screenshots below are historical.

## Latest revision — neutral black palette

The user's subsequent direction supersedes the original purple accent treatment. Branding, primary actions, navigation, focus, informational surfaces, empty states, dialogs, and the risk curve now use black/charcoal and neutral grey. Blue, green, amber, and red remain only as functional data/status colors; former purple event tokens are now neutral slate.

Latest evidence: `../design/qa/neutral.png` (1440 × 1000, DPR 1), compared with both supplied references in `../design/qa/neutral-comparison.jpg`. The combined comparison was opened and reviewed. Typography, spacing, imagery, and copy remain unchanged; no actionable visual regressions were identified. Computed primary-button colors are rgb(41, 41, 41) with white text. Strict TypeScript, the 700-line check, and the production build pass. The neutral preference is saved in `AGENTS.md`. Earlier screenshots below document the previous design iteration only.

## Comparison target

- Source truth: `/Users/mardonjon/Desktop/wiut/design/reference1.jpg` and `reference2.jpg`, both 1170 × 2532 pixels.
- This is an intentional traffic-dashboard adaptation of a desktop reference photographed inside a mobile social viewer, not a pixel-identical project-management clone. The app-owned reference regions are approximately y=625–1900; black viewer chrome and the landscape presentation background are excluded.
- Desktop implementation: `/Users/mardonjon/Desktop/wiut/design/qa/desktop.png`, 1440 × 1000 pixels, CSS viewport 1440 × 1000, device pixel ratio 1. State: dashboard, illustrative scenario, selected near-miss at 01:02.
- Lower desktop region: `/Users/mardonjon/Desktop/wiut/design/qa/events.png`, 1440 × 1000, same viewport and selection. Shows the entire timeline and expanded event table.
- Mobile implementation: `/Users/mardonjon/Desktop/wiut/design/qa/mobile.png`, 390 × 844, CSS viewport 390 × 844, device pixel ratio 1. State: dashboard, illustrative scenario.
- Combined visual comparison: `/Users/mardonjon/Desktop/wiut/design/qa/comparison.jpg`, 2000 × 1600. Source crops and the two implementation viewport captures were placed together and opened for visual comparison. Source crops preserve aspect ratio; implementation captures are uniformly downscaled. The original desktop reference viewport is unknown, so no pixel-perfect scale claim is made.
- The browser's full-page capture produced duplicated/scaled tiles under viewport emulation. Those captures were discarded. Two normal viewport screenshots provide the complete main-dashboard comparison instead.

## Findings and iteration history

1. **[P2, resolved] Small and faint secondary text.** The first implementation used overly small metadata and washed-out foreground colors. Increased regular labels/metadata and darkened text while preserving soft card backgrounds and status accents. Latest desktop and mobile captures show the correction.
2. **[P2, resolved] Cramped tablet summary cards.** At roughly 680 pixels wide, three cards compressed titles and badges. Stacked cards below 760 pixels and simplified card headers at intermediate widths. Mobile capture confirms readable cards without overlap.
3. **[P2, resolved] Mobile document overflow.** At 390 pixels, document scroll width was 634 pixels. An absolutely positioned screen-reader-only table label escaped the table scroll container. Making that container a positioning context fixed the cause; the measured document scroll width is now exactly 390 pixels. The table and timeline retain intentional internal scrolling.
4. **[P2, resolved] Timeline selection could be off the visible table page.** Selecting a later event now resets table filters and moves to the selected event's page. Verified EV-012 at 05:18 is visible after selecting its timeline segment.
5. **[P2, resolved] Offscreen mobile navigation remained keyboard reachable.** Closed mobile navigation is now inert; open navigation has a close button, Escape dismissal, focus restoration, and a bounded keyboard loop. Verified Escape returns the menu to its closed state.

No actionable P0/P1/P2 visual differences remain in the requested frontend scope.

## Required fidelity surfaces

- **Typography:** locally bundled Inter approximates the reference's neutral sans-serif. Compact medium-weight card headings and stronger page titles preserve hierarchy. The implementation intentionally increases metadata readability rather than reproducing screenshot blur. No overlapping text remains at checked widths.
- **Spacing/layout:** narrow persistent sidebar, inset main panel, three summary cards, outlined white surfaces, soft 7–12 pixel radii, restrained shadows, and consistent panel gaps carry the reference structure. A camera/risk row is intentionally added for the traffic task, moving the timeline further down the page.
- **Colors/tokens:** neutral grey shell, white cards, purple identity/action accent, and soft blue/green/amber/red semantic states. Critical events use red rather than the source's task-progress blue. Focus indicators and text contrast were strengthened.
- **Images/icons:** organizer camera still is a real source asset, labeled as a reference still. It is not used as event evidence. Sample cards explicitly share the reference image. Phosphor icons replace the source's task-specific icons. No invented faces, generated detections, or decorative scene drawings were introduced.
- **Copy/content:** English traffic-review terminology throughout. Preview values are explicitly illustrative. Local uploads do not claim model inference. Imported confidence/lane fields are not invented. Team member identities and model results remain honestly unprovided.

## Browser verification

- All four pages navigate correctly; all four original sample links are present.
- Search for near miss returns two matching events; severity Critical returns three events.
- Review toggling changes the event and summary count.
- Timeline selection seeks to the selected time, including a later-page event.
- A five-second local H.264 MP4 opens and plays to its end; automatic analysis remains empty.
- Valid official JSON imports an event and risk data. Selecting the imported event seeks local playback to 1 second.
- Out-of-duration JSON is rejected with a clear inline error, preserving existing results.
- Export was verified through an actual downloaded `preview-events.json` in Chrome: 12 events and an explicit illustrative-data note. The browser automation download-event listener timed out, but the downloaded artifact was independently read and validated.
- Mobile navigation opens/closes and Escape works. Document width matches viewport width at 390 pixels.
- Fresh Chrome console check after the final chart initialization fix returned no errors or warnings. Earlier Recharts initial-size warnings were resolved by supplying initial dimensions; historical in-app logs retain those older entries.
- Production build, strict TypeScript checks, six result-parser tests, and the source-size guard passed.

## Follow-up polish and practical limits

- [P3] Short event bars abbreviate labels; their full names remain available through accessible labels, hover titles, and event details. This preserves honest temporal widths.
- Automated inference, quantitative EDA, tracking overlays, calibrated risk, member profiles, and public deployment belong to Phase 2 or later and were not represented as finished.
- Source footage is not bundled; the dashboard uses the licensed/user-supplied reference still and original video links. Users can play their own local files.

## Implementation checklist

- [x] Reference-inspired desktop layout and responsive mobile layout.
- [x] Real local playback, verified import, filtering, review, and export.
- [x] Explicit illustrative-data boundaries and no fabricated model output.
- [x] Short, modular files and documented API/inference boundaries.
- [x] Final screenshots compared together with the supplied references.
- [x] Local preview left running for review; no public deployment performed.
