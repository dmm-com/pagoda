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
  return (
    <AironeModal
      title={"アイテム名の自動設定"}
      caption={"属性値からアイテム名を自動的に登録するための設定"}
      open={index >= 0}
      onClose={handleCloseModal}
    >
      <Table>
        <TableBody>
          {/* set attr.nameOrder */}
          <TableRow>
            <TableCell>名前に設定する順番</TableCell>
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
            <TableCell>名前に付ける接頭辞</TableCell>
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
            <TableCell>名前に付ける接尾辞</TableCell>
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
          <Typography align="right">閉じる</Typography>
        </Button>
      </Box>
    </AironeModal>
  );
};
