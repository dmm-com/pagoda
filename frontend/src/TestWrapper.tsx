import { createTheme, ThemeProvider } from "@mui/material/styles";
import { SnackbarProvider } from "notistack";
import { FC, ReactNode, StrictMode } from "react";
import { MemoryRouter } from "react-router";
import { SWRConfig } from "swr";

// Render under StrictMode like the app (see App.tsx), so that effects which
// are not idempotent fail in tests instead of only in the browser.
export const TestWrapper: FC<{ children: ReactNode }> = ({ children }) => {
  const theme = createTheme();
  return (
    <StrictMode>
      <SWRConfig
        value={{
          provider: () => new Map(),
          dedupingInterval: 0,
          revalidateOnFocus: false,
          revalidateOnReconnect: false,
        }}
      >
        <ThemeProvider theme={theme}>
          <SnackbarProvider maxSnack={1} autoHideDuration={100}>
            <MemoryRouter>{children}</MemoryRouter>
          </SnackbarProvider>
        </ThemeProvider>
      </SWRConfig>
    </StrictMode>
  );
};

export const TestWrapperWithoutRoutes: FC<{ children: ReactNode }> = ({
  children,
}) => {
  const theme = createTheme();
  return (
    <StrictMode>
      <SWRConfig
        value={{
          provider: () => new Map(),
          dedupingInterval: 0,
          revalidateOnFocus: false,
          revalidateOnReconnect: false,
        }}
      >
        <ThemeProvider theme={theme}>
          <SnackbarProvider maxSnack={1} autoHideDuration={100}>
            {children}
          </SnackbarProvider>
        </ThemeProvider>
      </SWRConfig>
    </StrictMode>
  );
};
