# External Input Failures

Use this guide when the evidence points to a value that crosses a system boundary: a server response, header, server-provided setting or text, push payload, deep link, or imported file.

- Confirm that a real external system can send the value. Check the protocol, API specification, server code, or observed traffic. A value outside the documented range still counts if nothing on the sending side rejects it; record that as `ASSUMED`.
- Deliver the value through the real input path: a mock server, recorded fixture, proxy rewrite, or test account setting. Keep the product's parsing and validation unchanged.
- Trace the value from the boundary to the crash site, and record each conversion on the way, such as string to number, number to duration, or text to range.
- Record the failure kind. A Swift runtime trap, such as overflow or a failed numeric conversion, and an Objective-C exception, such as `NSRangeException`, need different evidence and can't be caught the same way.
- Do not inject the value after the parser or validator, and do not send a value the protocol cannot carry.
