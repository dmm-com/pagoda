import { Box, Divider, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, ReactElement } from "react";

const Frame = styled(Box)(({}) => ({
  width: "100%",
  height: "284px",
}));

const Fixed = styled(Box)(({}) => ({
  position: "fixed",
  zIndex: 2,
  width: "100%",
  backgroundColor: "white",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
}));

const HeaderTop = styled(Box)(({ theme }) => ({
  width: theme.breakpoints.values.lg,
  height: "88px",
  marginTop: "124px",
  display: "flex",
}));

const HeaderBottom = styled(Box)(({ theme }) => ({
  width: theme.breakpoints.values.lg,
  height: "40px",
  display: "flex",
  alignItems: "flex-end",
}));

const TitleBox = styled(Box)(({}) => ({
  display: "flex",
  alignItems: "flex-end",
  margin: "8px 24px",
}));

const Title = styled(Typography)(({}) => ({
  height: "72px",
  maxWidth: "700px",
  overflow: "hidden",
  textOverflow: "ellipsis",
}));

interface Props {
  title: string;
  subTitle?: string;
  description?: string;
  componentSubmits: ReactElement<any>;
  componentControl?: ReactElement<any>;
}

export const PageHeader: FC<Props> = ({
  title,
  subTitle,
  description,
  componentControl,
  componentSubmits,
}) => {
  return (
    <Frame>
      <Fixed>
        <HeaderTop>
          <TitleBox>
            <Title variant="h2" mr="64px">
              {title}
            </Title>
            <Typography variant="h4" fontWeight="300">
              {subTitle}
            </Typography>
          </TitleBox>
          <Box ml="auto" mr="24px">
            {componentControl}
          </Box>
        </HeaderTop>
        <HeaderBottom>
          <Typography>{description}</Typography>
          <Box ml="auto" mr="24px">
            {componentSubmits}
          </Box>
        </HeaderBottom>
        <Divider flexItem sx={{ mt: "32px", borderColor: "black" }} />
      </Fixed>
    </Frame>
  );
};
