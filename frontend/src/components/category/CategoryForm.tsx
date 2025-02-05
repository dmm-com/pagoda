import {
  Autocomplete,
  Box,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TextField,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { Schema } from "./categoryForm/CategoryFormSchema";

import {
  HeaderTableCell,
  HeaderTableRow,
  StyledTableRow,
} from "components/common/Table";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { aironeApiClient } from "repository/AironeApiClient";

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

export const CategoryForm: FC<Props> = ({ control, setValue }) => {
  const entities = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntities();
  });

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
              <TableCell>カテゴリ名</TableCell>
              <TableCell>
                <Controller
                  name="name"
                  control={control}
                  defaultValue=""
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      id="category-name"
                      required
                      placeholder="カテゴリ名"
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

            <StyledTableRow>
              <TableCell>登録モデル(複数可)</TableCell>
              <TableCell>
                <Controller
                  name="models"
                  control={control}
                  defaultValue={[]}
                  render={({ field }) => (
                    <Autocomplete
                      {...field}
                      options={entities.value?.results ?? []}
                      disabled={entities.loading}
                      getOptionLabel={(option) => option.name}
                      isOptionEqualToValue={(option, value) =>
                        option.id === value.id
                      }
                      onChange={(_e, value: any) => {
                        setValue("models", value, {
                          shouldDirty: true,
                          shouldValidate: true,
                        });
                      }}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          variant="outlined"
                          placeholder="モデルを選択"
                        />
                      )}
                      multiple
                      disableCloseOnSelect
                      fullWidth
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
