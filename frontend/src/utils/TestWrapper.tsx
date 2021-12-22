import { createTheme, ThemeProvider } from "@mui/material/styles";
import React, { FC } from "react";
import { MemoryRouter } from "react-router-dom";

export const TestWrapper: FC = ({ children }) => {
  const theme = createTheme();
  return (
    <ThemeProvider theme={theme}>
      <MemoryRouter>{children}</MemoryRouter>
    </ThemeProvider>
  );
};
