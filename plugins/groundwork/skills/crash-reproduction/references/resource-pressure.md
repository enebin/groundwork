# Resource Pressure and Termination

Use this guide when the evidence points to memory pressure, resource exhaustion, watchdog termination, or operating-system killing.

- Reproduce with realistic content volume, scrolling, media use, backgrounding, and system memory-pressure events.
- Distinguish an operating-system termination such as out-of-memory killing from an in-process exception; they require different evidence.
- Compare memory growth, retained objects, CPU time, blocking duration, and system termination reports with the original incident.
- Do not allocate an unrealistic amount of memory or intentionally block execution solely to force termination.
