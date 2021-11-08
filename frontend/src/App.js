import React from "react";
import ReactDOM from "react-dom";

import { AppRouter } from "./AppRouter";
import { ErrorHandler } from "./ErrorHandler";

function App({}) {
  return (
    <ErrorHandler>
      <AppRouter />
    </ErrorHandler>
  );
}

ReactDOM.render(<App />, document.getElementById("app"));
