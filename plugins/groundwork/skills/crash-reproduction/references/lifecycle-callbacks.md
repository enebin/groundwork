# Lifecycle and Callback Failures

Use this guide when the evidence points to a callback, observer, timer, animation, or task arriving after its owner changes lifecycle state.

- Start the real operation, then dismiss the screen, navigate back, replace its content, log out, switch accounts, or background the app before completion.
- Slow only the pending operation, then allow its original completion path to run.
- Check whether cancellation, observer removal, ownership, and callback delivery match the state expected by the crashed code.
- Do not deliver a fabricated callback or manually invoke an observer method.
