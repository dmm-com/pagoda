import { styled } from "@mui/material/styles";
import { Link } from "react-router";

export const AironeLink = styled(Link)(({ theme }) => ({
  color: theme.palette.primary.main,
  textDecoration: "none",
  "&:hover": {
    textDecoration: "underline",
    color: theme.palette.secondary.main,
  },
}));
