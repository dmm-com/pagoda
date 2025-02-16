import { createTheme, ThemeProvider } from "@mui/material/styles";
import { SnackbarProvider } from "notistack";
import React, { FC } from "react";
import { MemoryRouter } from "react-router";

export const TestWrapper: FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const theme = createTheme();
  return (
    <ThemeProvider theme={theme}>
      <SnackbarProvider>
        <MemoryRouter>{children}</MemoryRouter>
      </SnackbarProvider>
    </ThemeProvider>
  );
};

export const TestWrapperWithoutRoutes: FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const theme = createTheme();
  return (
    <ThemeProvider theme={theme}>
      <SnackbarProvider>{children}</SnackbarProvider>
    </ThemeProvider>
  );
};
