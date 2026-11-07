# Input pack audit

The parser was run against the ZIP supplied in this conversation.

| Measure | Observed |
|---|---:|
| Text screenplay files | 50 |
| Episodes parsed | 50 / 50 |
| Scene blocks | 100 |
| Timed screenplay blocks | 3,727 |
| Camera blocks | 1,754 |
| Dialogue blocks | 1,487 |
| Action blocks | 372 |
| Sound-effect blocks | 114 |
| Shortest episode | 70.50 seconds |
| Longest episode | 200.75 seconds |
| Average episode duration | 123.25 seconds |
| Median episode duration | 117.785 seconds |

## Format variations handled

- Scene headings and labels appear in both title case and uppercase (for example, `Scene heading` and `SCENE HEADING`).
- Each timed block uses a `Start: (MM:SS.xx) | End: (MM:SS.xx)` line.
- Timed block labels identify camera direction, action, sound effects, or a speaking character.
- Episode loglines and continuity notes are available in all 50 parsed files.

The parser uses case-insensitive scene-header matching and reads ZIP members directly without extracting their paths to disk.
