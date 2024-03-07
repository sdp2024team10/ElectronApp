* select serial port from dropdown
* show confidence values
* allow nodejs to decide when picture is taken
* parallelize predictions
* prediction results json schema
* prediction status in frontent similar to verification status
* 8080 is still hard coded in script.js
* add PIDs to logs for subprocesses
* inconsistent handling of `message.data` / `message["data"]`
* break `handleIncomingWebSockMessage()` into separate functions
* substitute `ws.send` for `sendWebSockMessageToFrontend()`
* `if (process.platform !== 'darwin') app.quit()`: why would we decide not to quit when running on mac?
* indexes of predictions are off by one
* allow user to kill ongoing predictions
* undo/redo in expression boxes
* expression 5 is missing in example image:
```
predict.py stdout: {"type": "prediction-result", "data": {"index": 5, "latex": "\\pi i \\pi i \\pi i + \\sqrt { 4 ^ { 8 } + \\ldots } }", "time": "0:00:03.965647"}}
```
* ^^^ is it the trailing `}`?
* add button to clear all expressions
* verification results do not comply to schema:
```
"{\"all-equal\": false, \"equation1\": \"x^2\", \"equation2\": \"i\\\\pi i\\\\pi2+2=4\", \"first-non-equal-indexes\": [0, 1], \"x-axis-array\": [0.0, 1.1111111111111112, 2.2222222222222223, 3.3333333333333335, 4.444444444444445, 5.555555555555555, 6.666666666666667, 7.777777777777779, 8.88888888888889, 10.0], \"y-axis-array1\": [0.0, 1.234567901234568, 4.938271604938272, 11.111111111111112, 19.75308641975309, 30.864197530864196, 44.44444444444445, 60.49382716049384, 79.01234567901236, 100.0], \"y-axis-array2\": false}\n"
```
