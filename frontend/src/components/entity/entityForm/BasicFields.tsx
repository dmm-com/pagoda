import {
  Box,
  Checkbox,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TextField,
  Typography,
} from "@mui/material";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";

import { Schema } from "./EntityFormSchema";

import {
  HeaderTableRow,
  HeaderTableCell,
  StyledTableRow,
} from "components/common/Table";

interface Props {
  control: Control<Schema>;
}

export const BasicFields: FC<Props> = ({ control }) => {
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
