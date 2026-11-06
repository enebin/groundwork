# Collection and Snapshot Failures

Use this guide when the evidence points to an invalid index or disagreement between a model collection and its UI snapshot.

- Use legitimate add, remove, reorder, refresh, pagination, filtering, or cell-reuse actions that can overlap with a real data response.
- Slow the response or UI update that separates the collection snapshot from the access. Record both snapshots before changing any code.
- Check whether the crash requires an old index path, a reordered model, or an update applied twice.
- Do not inject an impossible index or mutate the collection directly from a debugger.
