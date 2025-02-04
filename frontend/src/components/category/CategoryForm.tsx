import {
  Autocomplete,
  Box,
  FormHelperText,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TextField,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller, FieldError } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { useAsyncWithThrow } from "../../hooks/useAsyncWithThrow";
import { aironeApiClient } from "../../repository/AironeApiClient";
import { ServerContext } from "../../services/ServerContext";

import { Schema } from "./categoryForm/CategoryFormSchema";

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

interface MyEntity {
  readonly id: number;
  readonly name: string;
}

export const CategoryForm: FC<Props> = ({ control, setValue }) => {
  const serverContext = ServerContext.getInstance();

  const entities = useAsyncWithThrow(async () => {
    const entities = await aironeApiClient.getEntities();
    return entities.results.map((x) => {
      return { id: x.id, name: x.name } as MyEntity;
    });
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

            <StyledTableRow>
              <TableCell>登録モデル(複数可)</TableCell>
              <TableCell>
                <Controller
                  name="models"
                  control={control}
                  defaultValue={[]}
                  render={({ field, fieldState: { error } }) => (
                    <Autocomplete
                      {...field}
                      options={entities.value ?? []}
                      disabled={entities.loading}
                      getOptionLabel={(option: MyEntity) => option.name}
                      isOptionEqualToValue={(
                        option: MyEntity,
                        value: MyEntity
                      ) => option.id === value.id}
                      onChange={(_e, value: any) => {
                        console.log("[onix/onChange] value:", value);
                        setValue("models", value, {
                          shouldDirty: true,
                          shouldValidate: true,
                        });
                      }}
                      renderInput={(params) => (
                        <Box>
                          <TextField {...params} variant="outlined" />
                          {/* NOTE: role schema will inject some nested errors. It shows the first. */}
                          {Array.isArray(error) && (
                            <>
                              {(() => {
                                const first = (error as FieldError[]).filter(
                                  (e) => e.message != null
                                )?.[0];
                                return (
                                  first != null && (
                                    <FormHelperText error>
                                      {first.message}
                                    </FormHelperText>
                                  )
                                );
                              })()}
                            </>
                          )}
                          {error != null && (
                            <FormHelperText error>
                              {error.message}
                            </FormHelperText>
                          )}
                        </Box>
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
