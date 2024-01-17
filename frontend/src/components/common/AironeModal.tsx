import { Box, Modal, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, ReactNode } from "react";

const StyledModal = styled(Modal)(({}) => ({
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
}));

const Paper = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  backgroundColor: theme.palette.background.paper,
  border: "2px solid #000",
  boxShadow: theme.shadows[5],
  padding: theme.spacing(2, 3, 1),
  width: "50%",
}));

interface Props {
  title: string;
  description?: string;
  caption?: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

export const AironeModal: FC<Props> = ({
  title,
  description,
  caption,
  open,
  onClose,
  children,
}) => {
  return (
    <StyledModal open={open} onClose={onClose}>
      <Paper id="modal">
        <Typography variant={"h6"} my="8px">
          {title}
        </Typography>
        {description && (
          <Typography variant={"body2"} my="4px">
            {description}
          </Typography>
        )}
        {caption && (
          <Typography variant={"caption"} my="4px">
            {caption}
          </Typography>
        )}

        <Box>{children}</Box>
      </Paper>
    </StyledModal>
  );
};
