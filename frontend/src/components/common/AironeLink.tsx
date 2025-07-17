import { styled } from "@mui/material/styles";
import { Link, LinkProps } from "react-router";

export const AironeLink: React.ComponentType<LinkProps> = styled(
  Link,
)<LinkProps>(({ theme }) => ({
  color: theme.palette.primary.main,
  textDecoration: "none",
  "&:hover": {
    textDecoration: "underline",
    color: theme.palette.secondary.main,
  },
}));
