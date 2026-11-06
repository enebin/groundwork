# Reentrancy and Duplicate Events

Use this guide when the evidence points to reentrancy, duplicate completion, retry, reconnection, or repeated user input.

- Look for real flows where a delegate or completion can synchronously start another operation, or where retry, reconnect, cancellation, and success can arrive close together.
- Use rapid repeated input only if the product actually accepts it. Use real retry or reconnection behavior rather than calling a completion twice by hand.
- Record the event order and identify the first point where the same transition is accepted more than once.
