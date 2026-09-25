import { Box, Button, TextField, Typography } from "@mui/material";
import { FC } from "react";
import { Control, Controller } from "react-hook-form";

import { AironeModal } from "../../common/AironeModal";

import { Schema } from "./EntityFormSchema";

import { useTranslation } from "hooks/useTranslation";

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
  const { t } = useTranslation();

  return (
    <AironeModal
      title={t("entity.form.attrDescriptionMenuTitle")}
      caption={t("entity.form.attrNoteModalCaption")}
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
            placeholder={t("entity.form.attrNotePlaceholder")}
            variant="standard"
            fullWidth
          />
        )}
      />

      <Box display="flex" justifyContent="flex-end">
        <Button onClick={handleCloseModal}>
          <Typography align="right">{t("common.close")}</Typography>
        </Button>
      </Box>
    </AironeModal>
  );
};
