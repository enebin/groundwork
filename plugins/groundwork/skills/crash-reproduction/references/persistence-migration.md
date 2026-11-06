# Persistence and Migration Failures

Use this guide when the evidence points to persisted data, cache restoration, or version migration.

- Produce the state with a real older app version, interrupted app lifecycle, supported import, or normal cached data, then launch or upgrade into the crashing version.
- Preserve a copy of the naturally produced state for repeated tests.
- Compare the stored schema and migration path with the version from the crash environment.
- Do not hand-edit a database or serialized file unless the evidence shows that the product itself can write that exact malformed state.
