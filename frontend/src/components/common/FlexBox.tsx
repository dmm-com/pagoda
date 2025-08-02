import { Box, BoxProps } from "@mui/material";
import { styled } from "@mui/material/styles";
import { SxProps, Theme } from "@mui/system";
import { ComponentType } from "react";

type StyledBoxProps = BoxProps & {
  sx?: SxProps<Theme>;
};

export const FlexBox: ComponentType<StyledBoxProps> = styled(
  Box,
)<StyledBoxProps>({
  display: "flex",
}) as ComponentType<StyledBoxProps>;

export const BetweenAlignedBox: ComponentType<StyledBoxProps> = styled(
  FlexBox,
)<StyledBoxProps>({
  justifyContent: "space-between",
}) as ComponentType<StyledBoxProps>;

export const RightAlignedBox: ComponentType<StyledBoxProps> = styled(
  FlexBox,
)<StyledBoxProps>({
  justifyContent: "end",
}) as ComponentType<StyledBoxProps>;

export const CenterAlignedBox: ComponentType<StyledBoxProps> = styled(
  FlexBox,
)<StyledBoxProps>({
  justifyContent: "center",
}) as ComponentType<StyledBoxProps>;
