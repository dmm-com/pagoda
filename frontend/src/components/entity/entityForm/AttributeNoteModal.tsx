import { Box, Button, Modal, TextField, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";

import { Schema } from "./EntityFormSchema";

const StyledModal = styled(Modal)(({}) => ({
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
}));

const Paper = styled(Box)(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  border: "2px solid #000",
  boxShadow: theme.shadows[5],
  padding: theme.spacing(2, 4, 3),
  width: "50%",
}));

interface Props {
  index: number;
  handleCloseModal: () => void;
  control: Control<Schema>;
}

export const AttributeNoteModal: FC<Props> = ({
  index,
  handleCloseModal,
  control,
}) => {
  return (
    <StyledModal open={index >= 0} onClose={handleCloseModal}>
      <Paper>
        <Typography variant={"h6"}>属性説明</Typography>
        <Typography variant={"caption"}>必要に応じてご入力ください</Typography>
        <Controller
          name={`attrs.${index}.note`}
          control={control}
          defaultValue={""}
          render={({ field }) => (
            <TextField
              {...field}
              placeholder="説明"
              variant="standard"
              fullWidth
            />
          )}
        />

        <Box display="flex" justifyContent="flex-end">
          <Button onClick={handleCloseModal}>
            <Typography align="right">閉じる</Typography>
          </Button>
        </Box>
      </Paper>
    </StyledModal>
  );
};
