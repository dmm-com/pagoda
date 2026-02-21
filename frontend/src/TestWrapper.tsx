import { createTheme, ThemeProvider } from "@mui/material/styles";
import { SnackbarProvider } from "notistack";
import { FC, ReactNode } from "react";
import { MemoryRouter } from "react-router";
import { SWRConfig } from "swr";

export const TestWrapper: FC<{ children: ReactNode }> = ({ children }) => {
  const theme = createTheme();
  return (
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
      <ThemeProvider theme={theme}>
        <SnackbarProvider maxSnack={1} autoHideDuration={100}>
          <MemoryRouter>{children}</MemoryRouter>
        </SnackbarProvider>
      </ThemeProvider>
    </SWRConfig>
  );
};

export const TestWrapperWithoutRoutes: FC<{ children: ReactNode }> = ({
  children,
}) => {
  const theme = createTheme();
  return (
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
      <ThemeProvider theme={theme}>
        <SnackbarProvider maxSnack={1} autoHideDuration={100}>
          {children}
        </SnackbarProvider>
      </ThemeProvider>
    </SWRConfig>
  );
};
