# Usability heuristics for rendered sessions

What an agent on the running app judges when it looks at usability, and how it rates what it finds. `ux-persona-reviewer` and `ux-journey-tester` both use this file. `ux-flow-reviewer` keeps its own code-based checklist and change-relative severity.

## What to judge

For each task or journey step:

- **Understanding.** Can the user tell where they are and what state things are in? Are counts, statuses, labels, and the next action clear? Are similar things clearly distinguished?
- **Discoverability.** Can the user find the start of the task without help? Are important actions hidden behind menus, scrolling, or overflow?
- **Steps.** Are there avoidable steps, repeated input, or dead ends?
- **Feedback.** Does the user know an action succeeded, is in progress, or was saved?
- **Recovery.** Can the user recover from wrong input, failure, an unavailable resource, or a disconnected state? Are destructive actions clear about their consequence and reversible where expected?
- **Physical reach.** Touch target size, keypad and keyboard reach, modal and sheet reachability, focus, and scrolling on each device size the user has.
- **Content stress.** Long names, many items, empty lists, and error states.
- **Reset.** On shared devices, the next person does not see the previous person's input.

Pixel fidelity against the design source belongs to `ui-qa`. Exact copy wording belongs to `writing-reviewer`. What the UI shows does not establish API privacy or authorization; that belongs to `security-reviewer`.

## Severity

Rate each obstacle by what happened to the user at that point, not by how often you expect it:

- 🔴 Critical: the user cannot finish the task or reach the next part of the journey, and no visible path exists. This includes a group of users, such as keyboard-only or screen-reader users, who are locked out.
- 🟠 Major: the user finishes, but only after being misled (a failed action looked done, or the screen showed stale or wrong values), stuck with no explanation (a primary action disabled or an input rejected with no visible reason), forced onto a hidden path or a backtrack on a core step, or able to destroy data with no confirmation or undo.
- 🟡 Minor: friction that neither blocks nor misleads: a hesitation while the path stays visible, an extra step, a missing hint, a small accessibility gap with a visible alternative.

Do not lower a rating because you guessed your way past the obstacle, and do not raise one for taste. Taste-only points are nits and go with preferences, not defects.
