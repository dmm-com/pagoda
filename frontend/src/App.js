import React from "react";
import ReactDOM from "react-dom";

import { AppRouter } from "./AppRouter.tsx";
import { ErrorHandler } from "./ErrorHandler.tsx";

function App({}) {
  return (
    <ErrorHandler>
      <AppRouter />
    </ErrorHandler>
  );
}

ReactDOM.render(<App />, document.getElementById("app"));
