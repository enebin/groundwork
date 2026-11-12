# Memory Lifetime Failures

Use this guide when the evidence points to access after an object lifetime ends, a dangling pointer, or use-after-free.

The goal is to make an ordinary object lifetime end while real work that still refers to it remains pending:

1. Identify where the object is created, where its lifetime normally ends, and which callback, delegate, observer, timer, task, or queued block may access it later.
2. Start that work through the normal UI or system flow.
3. Keep the work pending with a slow network, delayed response, breakpoint, or a local delay at the real asynchronous boundary.
4. End the object's lifetime through a valid action such as dismissing the screen, navigating back, logging out, switching accounts, replacing a child controller, reloading a list, or scrolling until a cell is reused.
5. Resume the real callback or event and observe whether it accesses the expired object.
6. Repeat the same valid sequence. Use ordinary memory pressure or realistic scrolling and allocation activity when reuse of the freed memory appears relevant.

Where available, use Zombies for Objective-C object lifetime errors and Address Sanitizer, Guard Malloc, Malloc Scribble, or allocation history for invalid memory access. These tools can change allocation and timing. A diagnostic report supports the hypothesis but does not by itself prove an exact reproduction; compare its access path and object lifetime with the original crash.

Never call `deinit`, `dealloc`, `free`, or `release` solely to shorten the lifetime. Do not retain a raw pointer and access it manually. The lifetime must end through a path the product can naturally take.
