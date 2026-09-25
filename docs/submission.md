# Submission readiness — 25 September 2026

Source specifications: [full task](task.md), [submission package](package.md). This is an evidence checklist, not a claim of complete accuracy.

## Implemented and verified locally

- Exact root interface; unchanged organizer harness and evaluator.
- Three local hash-pinned checkpoints, 139.1 MB; atomic verified download via `weights/download.sh`, with an offline `--check` option.
- Twelve active category paths on the inspected camera. All fourteen labels have implementation paths and configurable scene requirements; illegal turns and U-turns remain inactive pending prohibition facts. See [class evidence](classes.md).
- All four original samples processed again with expanded rules: C3896 114, C3897 99, C3902 98, C3905 42 candidate events. Combined predictions pass format validation: 353 events, zero errors/warnings.
- Full annotated playback, risk curves, timelines and measured maps in a permanent archive. Anonymous read endpoints are separate from expiring private upload jobs. Cookie loss and upload cleanup do not delete the sample gallery.
- Website report with measured findings, concrete failure evidence, learned-versus-rule-based explanation, dataset/checkpoint sources and licences, direct pinned model downloads and anonymous sample-prediction downloads.
- Team names and the supplied profiles are displayed. Unconfirmed contributions/URLs remain explicitly unclaimed.
- Explicit seeds and platform nondeterminism documented in README.
- Reproducible release packaging: `python -m scripts.package` produces `weights.tar`, `samples.tar` and checksums, excluding private uploads and raw source footage.

## Still unresolved

1. **Two real-camera category mappings:** authoritative prohibited lane-to-exit turns and no-U-turn zones. Controlled positive/negative tests verify the code, but do not establish these legal facts.
2. **Accuracy:** independent reviewed labels, temporal F1, false-negative analysis and calibrated anticipation remain outstanding. More candidate events does not prove better performance. Generic debris, hidden signal heads, wheel/contact geometry and occlusion remain limitations.
3. **Team attribution:** captain and names are confirmed; exact individual technical contributions, remaining GitHub/LinkedIn URLs and prior-project attribution still need the team's input.
4. **Public release and host:** a private repository does not provide anonymous GitHub downloads. Public visibility/release is an explicit pending decision. The website backend still needs an actual public hosting target; localhost links alone are not publicly reachable.
5. **Judging environment:** final all-sample repeated A+B harness checks and intended NVIDIA runtime/driver verification remain outstanding. Earlier Linux offline smoke tests do not establish target GPU performance.

## Validation distinction

Engineering tests exercise state, boundaries, negative cases, private/public data separation, caching, causal state and package integrity. `evaluate.py --validate-only` checks the output schema; neither establishes traffic-event accuracy. Part B is optional and its current conflict score remains uncalibrated.

The earlier six-category sample outputs and historical timing tables have been superseded by the expanded-rule run for website demonstrations. Keep the earlier benchmark logs as historical evidence, not measurements of a different revision.
