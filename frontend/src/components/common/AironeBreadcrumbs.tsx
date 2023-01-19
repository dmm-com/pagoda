import { Box, Breadcrumbs } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

const Frame = styled(Box)(({}) => ({
  width: "100%",
  height: "56px",
}));

const Fixed = styled(Box)(({}) => ({
  position: "fixed",
  zIndex: 2,
  width: "100%",
  backgroundColor: "white",
  display: "flex",
  justifyContent: "center",
}));

const BreadcrumbsBox = styled(Box)(({ theme }) => ({
  width: theme.breakpoints.values.lg,
  "& nav": {
    display: "flex",
    height: "56px",
    padding: "0px 24px",
  },
  "& li": {
    maxWidth: "300px",
    textOverflow: "ellipsis",
    overflow: "hidden",
    whiteSpace: "nowrap",
  },
  "& li > p": {
    textOverflow: "ellipsis",
    overflow: "hidden",
  },
}));

export const AironeBreadcrumbs: FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  return (
    <Frame>
      <Fixed>
        <BreadcrumbsBox>
          <Breadcrumbs aria-label="breadcrumb">{children}</Breadcrumbs>
        </BreadcrumbsBox>
      </Fixed>
    </Frame>
  );
};
