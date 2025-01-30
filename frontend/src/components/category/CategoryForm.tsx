import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { ServerContext } from "../../services/ServerContext";

import { Schema } from "./categoryForm/CategoryFormSchema";

import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TextField
} from "@mui/material";

import {
  HeaderTableCell,
  HeaderTableRow,
  StyledTableRow,
} from "components/common/Table";

const StyledBox = styled(Box)(({ theme }) => ({
  width: theme.breakpoints.values.lg,
  margin: "0 auto",
  marginBottom: "60px",
  display: "flex",
  flexDirection: "column",
  gap: "60px",
}));

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
}

export const CategoryForm: FC<Props> = ({
  control,
  setValue,
}) => {
  const serverContext = ServerContext.getInstance();

  return (
    <StyledBox>
      <Box>
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
                      minRows={5}
                      multiline
                      required
                      placeholder="備考"
                      error={error != null}
                      helperText={error?.message}
                      size="small"
                      fullWidth
                      inputProps={{ sx: { resize: "vertical" } }}
                    />
                  )}
                />
              </TableCell>
            </StyledTableRow>
          </TableBody>
        </Table>
      </Box>

    </StyledBox>
  );
};