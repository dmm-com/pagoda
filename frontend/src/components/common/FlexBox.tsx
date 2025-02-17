import { Box, BoxProps } from "@mui/material";
import { styled } from "@mui/material/styles";
import { SxProps, Theme } from "@mui/system";
import React from "react";

type StyledBoxProps = BoxProps & {
  sx?: SxProps<Theme>;
};

export const FlexBox: React.ComponentType<StyledBoxProps> = styled(
  Box
)<StyledBoxProps>({
  display: "flex",
}) as React.ComponentType<StyledBoxProps>;

export const BetweenAlignedBox: React.ComponentType<StyledBoxProps> = styled(
  FlexBox
)<StyledBoxProps>({
  justifyContent: "space-between",
}) as React.ComponentType<StyledBoxProps>;

export const RightAlignedBox: React.ComponentType<StyledBoxProps> = styled(
  FlexBox
)<StyledBoxProps>({
  justifyContent: "end",
}) as React.ComponentType<StyledBoxProps>;

export const CenterAlignedBox: React.ComponentType<StyledBoxProps> = styled(
  FlexBox
)<StyledBoxProps>({
  justifyContent: "center",
}) as React.ComponentType<StyledBoxProps>;
