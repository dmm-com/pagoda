import { Box, Button, TextField, Typography } from "@mui/material";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";

import { AironeModal } from "../../common/AironeModal";

import { Schema } from "./EntityFormSchema";

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
    <AironeModal
      title={"属性説明"}
      caption={"必要に応じてご入力ください"}
      open={index >= 0}
      onClose={handleCloseModal}
    >
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
    </AironeModal>
  );
};
