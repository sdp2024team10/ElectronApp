* select serial port from dropdown
* show confidence values
* allow nodejs to decide when picture is taken
* parallelize predictions
* prediction results json schema
* send more information to the `status` box on the frontend
* 8080 is still hard coded in script.js
* add PIDs to logs for subprocesses
* inconsistent handling of `message.data` / `message["data"]`
* break `handleIncomingWebSockMessage()` into separate functions
* substitute `ws.send` for `sendWebSockMessageToFrontend()`
* `if (process.platform !== 'darwin') app.quit()`: why would we decide not to quit when running on mac?
* allow user to kill ongoing predictions
* undo/redo in expression boxes
* add button to clear all expressions
* handle infinity in verification, x^-2=inf
* error if more than one unknown variable
* equalities
* vertical lines
