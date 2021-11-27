import React from "react";
import { FC } from "react";
import ReactDOM from "react-dom";

import { AppRouter } from "./AppRouter";
import { ErrorHandler } from "./ErrorHandler";

const App: FC = () => {
  return (
    <ErrorHandler>
      <AppRouter />
    </ErrorHandler>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
