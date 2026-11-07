# Manual quality review guide

The screenplays describe intended scenes, but they do not prove how a finished video looks or feels. Before submitting the AI run, review the top recommendations against the actual episodes.

## Review each candidate

1. Open the episode video and go to the suggested start timestamp.
2. Watch from the start through the end timestamp, including the first 3 seconds and the final 8 seconds.
3. Ask whether a viewer who has never seen the show can understand the basic conflict.
4. Check that the clip stops before the central question or conflict is resolved.
5. Record `yes` or `no` in `quality_review_template.csv` and explain why.

## Useful failure labels

- `weak_hook`: the opening is slow, unclear, or not attention-grabbing.
- `not_standalone`: character relationships or stakes are impossible to understand without prior episodes.
- `resolved_ending`: the clip ends after the dramatic question is answered.
- `weak_emotion`: the script moment reads dramatically but does not play strongly on screen.
- `timestamp_mismatch`: the time range cuts the wrong visual/dialogue beat.
- `unsupported_summary`: the model's hook, cliffhanger, or explanation is not supported by the script/video.
- `duplicate`: another candidate is effectively the same moment.

## Report a simple quality measure

For the top 10 candidates:

`Top-10 approval rate = number of human-approved candidates / 10`

Example: if 7 of the top 10 are useful, report 70% on this small review set. Do not call this a general accuracy score; the sample is small and only covers the top-ranked clips. Also record the most common rejection reason.

## What to include in the two-page write-up

- How many episodes were processed successfully.
- How many valid candidates were produced.
- How many of the top 10 candidates a human editor approved.
- One specific example where the model chose badly, with episode and timestamp.
- What the human reviewer noticed that the model missed.
- The limitation that the screenplay cannot reveal actual performance, visual quality, pacing, or editing.
