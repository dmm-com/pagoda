import { createTheme, ThemeProvider } from "@mui/material/styles";
import React from "react";
import { MemoryRouter } from "react-router-dom";

export function TestWrapper({ children }) {
  const theme = createTheme();
  return (
    <ThemeProvider theme={theme}>
      <MemoryRouter>{children}</MemoryRouter>
    </ThemeProvider>
  );
}
