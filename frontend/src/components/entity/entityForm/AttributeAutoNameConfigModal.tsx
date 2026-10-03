import {
  Box,
  Button,
  TextField,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "@mui/material";
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

export const AttributeAutoNameConfigModal: FC<Props> = ({
  index,
  handleCloseModal,
  control,
}) => {
  const { t } = useTranslation();

  return (
    <AironeModal
      title={t("entity.form.autoNameConfigTitle")}
      caption={t("entity.form.autoNameConfigCaption")}
      open={index >= 0}
      onClose={handleCloseModal}
    >
      <Table>
        <TableBody>
          {/* set attr.nameOrder */}
          <TableRow>
            <TableCell>{t("entity.form.nameOrderLabel")}</TableCell>
            <TableCell>
              <Controller
                name={`attrs.${index}.nameOrder`}
                control={control}
                defaultValue={"0"}
                render={({ field, fieldState: { error } }) => (
                  <TextField
                    {...field}
                    type="number"
                    id="name_order"
                    value={Number(field.value) ?? 0}
                    error={error != null}
                    helperText={error?.message}
                    size="small"
                    fullWidth
                    inputProps={{ "data-1p-ignore": true }}
                  />
                )}
              />
            </TableCell>
          </TableRow>

          {/* set attr.namePrefix */}
          <TableRow>
            <TableCell>{t("entity.form.namePrefixLabel")}</TableCell>
            <TableCell>
              <Controller
                name={`attrs.${index}.namePrefix`}
                control={control}
                defaultValue={"0"}
                render={({ field, fieldState: { error } }) => (
                  <TextField
                    {...field}
                    id="name_prefix"
                    error={error != null}
                    helperText={error?.message}
                    size="small"
                    fullWidth
                    inputProps={{ "data-1p-ignore": true }}
                  />
                )}
              />
            </TableCell>
          </TableRow>

          {/* set attr.namePostfix */}
          <TableRow>
            <TableCell>{t("entity.form.namePostfixLabel")}</TableCell>
            <TableCell>
              <Controller
                name={`attrs.${index}.namePostfix`}
                control={control}
                defaultValue={"0"}
                render={({ field, fieldState: { error } }) => (
                  <TextField
                    {...field}
                    id="name_postfix"
                    error={error != null}
                    helperText={error?.message}
                    size="small"
                    fullWidth
                    inputProps={{ "data-1p-ignore": true }}
                  />
                )}
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>

      <Box display="flex" justifyContent="flex-end">
        <Button onClick={handleCloseModal}>
          <Typography align="right">{t("common.close")}</Typography>
        </Button>
      </Box>
    </AironeModal>
  );
};
