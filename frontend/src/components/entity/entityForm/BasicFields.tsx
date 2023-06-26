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
}));

interface Props {
  control: Control<Schema>;
}

export const BasicFields: FC<Props> = ({ control }) => {
  return (
    <Box mb="80px">
      <Box my="16px">
        <Typography variant="h4" align="center">
          基本情報
        </Typography>
      </Box>

      <Table className="table table-bordered">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell>項目</HeaderTableCell>
            <HeaderTableCell>内容</HeaderTableCell>
          </HeaderTableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>エンティティ名</TableCell>
            <TableCell>
              <Controller
                name="name"
                control={control}
                defaultValue=""
                render={({ field, fieldState: { error } }) => (
                  <TextField
                    {...field}
                    required
                    placeholder="エンティティ名"
                    error={error != null}
                    helperText={error?.message}
                    sx={{ width: "100%" }}
                  />
                )}
              />
            </TableCell>
          </TableRow>
          <TableRow>
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
                    sx={{ width: "100%" }}
                  />
                )}
              />
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>サイドバーに表示</TableCell>
            <TableCell>
              <Controller
                name="isToplevel"
                control={control}
                defaultValue={false}
                render={({ field }) => (
                  <Checkbox
                    checked={field.value}
                    onChange={(e) => field.onChange(e.target.checked)}
                  />
                )}
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Box>
  );
};
