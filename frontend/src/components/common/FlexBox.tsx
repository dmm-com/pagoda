import { Box } from "@mui/material";
import { styled } from "@mui/material/styles";

export const FlexBox = styled(Box)(({}) => ({
  display: "flex",
}));

export const BetweenAlignedBox = styled(FlexBox)(({}) => ({
  justifyContent: "space-between",
}));

export const RightAlignedBox = styled(FlexBox)(({}) => ({
  justifyContent: "end",
}));

export const CenterAlignedBox = styled(FlexBox)(({}) => ({
  justifyContent: "center",
}));
