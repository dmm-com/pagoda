import { Box, CircularProgress, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

const LoadingBox = styled(Box)(({ theme }) => ({
  margin: "auto",
  padding: theme.spacing(1),
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
}));

const Text = styled(Typography)(({ theme }) => ({
  padding: theme.spacing(1),
}));

export const Loading: FC = () => {
  return (
    <Box data-testid="loading">
      <LoadingBox>
        <CircularProgress />
        <Text>Loading...</Text>
      </LoadingBox>
    </Box>
  );
};
