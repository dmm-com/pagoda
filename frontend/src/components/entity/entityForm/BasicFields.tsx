import {
  Box,
  Checkbox,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";

import { Schema } from "./EntityFormSchema";

const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({}) => ({
  color: "#FFFFFF",
  boxSizing: "border-box",
}));

const StyledTableRow = styled(TableRow)(({}) => ({
  "& td": {
    padding: "8px",
  },
}));

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
