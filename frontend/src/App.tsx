import React from "react";
import { createRoot } from "react-dom/client";

import { AppBase } from "AppBase";

const container = document.getElementById("app");
if (container == null) {
  throw new Error("failed to initializer React app.");
}
const root = createRoot(container);
root.render(<AppBase />);
