import { Box } from "@mui/material";
import { styled } from "@mui/material/styles";

export const FlexBox = styled(Box)(({}) => ({
  display: "flex",
}));

export const RightAlignedBox = styled(FlexBox)(({}) => ({
  justifyContent: "end",
}));

export const CenterAlignedBox = styled(FlexBox)(({}) => ({
  justifyContent: "center",
}));
