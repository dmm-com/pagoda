import {
  Box,
  Checkbox,
  FormControl,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TextField,
  Typography,
} from "@mui/material";
import { FC } from "react";
import { Control, Controller, useWatch } from "react-hook-form";

import { Schema } from "./EntityFormSchema";

import {
  HeaderTableCell,
  HeaderTableRow,
  StyledTableRow,
} from "components/common/Table";

interface Props {
  control: Control<Schema>;
}

export const BasicFields: FC<Props> = ({ control }) => {
  const currItemNameType = useWatch({ control, name: "itemNameType" });

  return (
    <Box>
      <Typography variant="h4" align="center" my="16px">
        基本情報
      </Typography>

      <Table className="table table-bordered">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell width="400px">項目</HeaderTableCell>
            <HeaderTableCell width="800px">内容</HeaderTableCell>
          </HeaderTableRow>
        </TableHead>
        <TableBody>
          <StyledTableRow>
            <TableCell>モデル名</TableCell>
            <TableCell>
              <Controller
                name="name"
                control={control}
                defaultValue=""
                render={({ field, fieldState: { error } }) => (
                  <TextField
                    {...field}
                    id="entity-name"
                    required
                    placeholder="モデル名"
                    error={error != null}
                    helperText={error?.message}
                    size="small"
                    fullWidth
                    inputProps={{ "data-1p-ignore": true }}
                  />
                )}
              />
            </TableCell>
          </StyledTableRow>
          <StyledTableRow>
            <TableCell>備考</TableCell>
            <TableCell>
              <Controller
                name="note"
                control={control}
                defaultValue=""
                render={({ field, fieldState: { error } }) => (
                  <TextField
                    {...field}
                    required
                    placeholder="備考"
                    error={error != null}
                    helperText={error?.message}
                    size="small"
                    fullWidth
                  />
                )}
              />
            </TableCell>
          </StyledTableRow>
          <StyledTableRow>
            <TableCell>アイテム名の登録方法</TableCell>
            <TableCell>
              <Controller
                name="itemNameType"
                control={control}
                defaultValue="US"
                render={({ field, fieldState: { error } }) => {
                  const itemNameType = useWatch({
                    control,
                    name: "itemNameType",
                  });

                  return (
                    <FormControl sx={{ m: 0, minWidth: 120 }} size="small">
                      <Select
                        id="itemNameType"
                        defaultValue={itemNameType}
                        onChange={(e) => {
                          field.onChange(e.target.value);
                        }}
                      >
                        <MenuItem value={"US"}>利用者が手動で設定</MenuItem>
                        <MenuItem value={"ID"}>UUIDに自動で設定</MenuItem>
                        <MenuItem value={"AT"}>
                          属性値に応じて自動で設定
                        </MenuItem>
                      </Select>
                    </FormControl>
                  );
                }}
              />
            </TableCell>
          </StyledTableRow>
          <StyledTableRow>
            <TableCell>
              <Typography
                color={
                  currItemNameType !== "US" ? "text.disabled" : "text.primary"
                }
              >
                アイテム名の許可パターン
              </Typography>
            </TableCell>
            <TableCell>
              <Controller
                name="itemNamePattern"
                control={control}
                defaultValue=""
                render={({ field, fieldState: { error } }) => {
                  return (
                    <TextField
                      {...field}
                      disabled={currItemNameType !== "US"}
                      required
                      placeholder="アイテム名の許可パターン"
                      error={error != null}
                      helperText={error?.message}
                      size="small"
                      fullWidth
                    />
                  );
                }}
              />
            </TableCell>
          </StyledTableRow>
          <StyledTableRow>
            <TableCell>トップページに表示</TableCell>
            <TableCell>
              <Controller
                name="isToplevel"
                control={control}
                defaultValue={false}
                render={({ field }) => (
                  <Checkbox
                    data-testid="isToplevel"
                    checked={field.value}
                    onChange={(e) => field.onChange(e.target.checked)}
                  />
                )}
              />
            </TableCell>
          </StyledTableRow>
        </TableBody>
      </Table>
    </Box>
  );
};
