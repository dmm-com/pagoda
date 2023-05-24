import { Box, Divider, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

const Frame = styled(Box)({
  width: "100%",
  height: "80px",
});

const Fixed = styled(Box)({
  position: "fixed",
  zIndex: 2,
  width: "100%",
  backgroundColor: "white",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
});

const Header = styled(Box)(({ theme }) => ({
  width: theme.breakpoints.values.lg,
  display: "flex",
  alignItems: "baseline",
  marginBottom: "16px",
}));

const Title = styled(Typography)({
  margin: "0 24px",
  maxWidth: "700px",
  overflow: "hidden",
  textOverflow: "ellipsis",
  fontWeight: "bold",
});

const ChildrenBox = styled(Box)({
  marginLeft: "auto",
  marginRight: "24px",
});

interface Props {
  title: string;
  description?: string;
  children?: React.ReactNode;
}

export const PageHeader: FC<Props> = ({ title, description, children }) => {
  return (
    <Frame>
      <Fixed>
        <Header>
          <Title id="title" variant="h6">
            {title}
          </Title>
          <Typography id="description" variant="subtitle1">
            {description}
          </Typography>
          <ChildrenBox>{children}</ChildrenBox>
        </Header>
        <Divider flexItem />
      </Fixed>
    </Frame>
  );
};
