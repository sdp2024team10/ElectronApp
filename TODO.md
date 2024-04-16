* ELECTRONAPP
* select serial port from dropdown (i think we want to reduce manual selection of the user and keep it one port)
* 8080 is still hard coded in script.js (done)
* add PIDs to logs for subprocesses 
* inconsistent handling of `message.data` / `message["data"]`
* break `handleIncomingWebSockMessage()` into separate functions
* substitute `ws.send` for `sendWebSockMessageToFrontend()`
* `if (process.platform !== 'darwin') app.quit()`: why would we decide not to quit when running on mac?
* allow user to kill ongoing predictions

* MAYBES
* show confidence values
* send more information to the `status` box on the frontend

* VERIF.py 
* handle infinity in verification, x^-2=inf
* error if more than one unknown variable
* equalities
* vertical lines
* undefined values in plot: remove from all graphs and print message to user showing undefined ranges/points

* CoMER git submodule (for what?)
