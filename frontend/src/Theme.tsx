import { createTheme } from "@mui/material/styles";
export const theme = createTheme({
  palette: {
    primary: {
      main: "#607D8B",
    },
    secondary: {
      main: "#90CAF9",
    },
    success: {
      main: "#1B76D2",
    },
    error: {
      main: "#B00020",
    },
    background: {
      default: "#607D8B",
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1064,
      xl: 1536,
    },
  },
  typography: {
    fontFamily: "Noto Sans JP",
  },
});
