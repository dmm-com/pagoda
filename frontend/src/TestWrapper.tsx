import { createTheme, ThemeProvider } from "@mui/material/styles";
import { SnackbarProvider } from "notistack";
import { FC, ReactNode } from "react";
import { MemoryRouter } from "react-router";

export const TestWrapper: FC<{ children: ReactNode }> = ({ children }) => {
  const theme = createTheme();
  return (
    <ThemeProvider theme={theme}>
      <SnackbarProvider maxSnack={1} autoHideDuration={100}>
        <MemoryRouter>{children}</MemoryRouter>
      </SnackbarProvider>
    </ThemeProvider>
  );
};

export const TestWrapperWithoutRoutes: FC<{ children: ReactNode }> = ({
  children,
}) => {
  const theme = createTheme();
  return (
    <ThemeProvider theme={theme}>
      <SnackbarProvider maxSnack={1} autoHideDuration={100}>
        {children}
      </SnackbarProvider>
    </ThemeProvider>
  );
};
