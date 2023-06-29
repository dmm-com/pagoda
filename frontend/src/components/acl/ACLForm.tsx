import {
  Box,
  FormHelperText,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller, useFieldArray } from "react-hook-form";
import { UseFormWatch } from "react-hook-form/dist/types/form";

import { Schema } from "components/acl/aclForm/ACLFormSchema";
import { DjangoContext } from "services/DjangoContext";

interface Props {
  control: Control<Schema>;
  watch: UseFormWatch<Schema>;
}

const HeaderTableRow = styled(TableRow)(() => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCellItem = styled(TableCell)(() => ({
  color: "#FFFFFF",
  width: "328px",
}));

const HeaderTableCellContext = styled(TableCell)(() => ({
  color: "#FFFFFF",
}));

const HeaderTableCellNote = styled(TableCell)(() => ({
  color: "#FFFFFF",
  width: "363px",
}));

export const ACLForm: FC<Props> = ({ control, watch }) => {
  const djangoContext = DjangoContext.getInstance();

  const { fields } = useFieldArray({
    control,
    name: "roles",
  });

  return (
    <Box>
      <Table className="table table-bordered">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCellItem>項目</HeaderTableCellItem>
            <HeaderTableCellContext>内容</HeaderTableCellContext>
          </HeaderTableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>公開設定</TableCell>
            <TableCell>
              <Controller
                name="isPublic"
                control={control}
                defaultValue={true}
                render={({ field, fieldState: { error } }) => (
                  <Box>
                    <Select
                      {...field}
                      fullWidth={true}
                      value={field.value ? 1 : 0}
                      onChange={(e) => field.onChange(e.target.value === 1)}
                      MenuProps={{ disableScrollLock: true }}
                    >
                      <MenuItem value={1}>公開</MenuItem>
                      <MenuItem value={0}>限定公開</MenuItem>
                    </Select>

                    {error != null && (
                      <FormHelperText error>{error.message}</FormHelperText>
                    )}
                  </Box>
                )}
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>

      <Box>
        <Box my="32px">
          <Typography variant="h4" align="center">
            公開制限設定
          </Typography>
        </Box>

        <Table className="table table-bordered">
          <TableHead>
            <HeaderTableRow>
              <HeaderTableCellItem>ロール</HeaderTableCellItem>
              <HeaderTableCellNote>備考</HeaderTableCellNote>
              <HeaderTableCellContext />
            </HeaderTableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell>全員</TableCell>
              <TableCell />
              <TableCell>
                <Controller
                  control={control}
                  name="defaultPermission"
                  defaultValue={djangoContext?.aclTypes.nothing.value}
                  render={({ field }) => (
                    <Select
                      {...field}
                      fullWidth={true}
                      disabled={watch("isPublic")}
                      MenuProps={{ disableScrollLock: true }}
                    >
                      {Object.keys(djangoContext?.aclTypes ?? {}).map(
                        (key, index) => (
                          <MenuItem
                            key={index}
                            value={djangoContext?.aclTypes[key].value}
                          >
                            {djangoContext?.aclTypes[key].name}
                          </MenuItem>
                        )
                      )}
                    </Select>
                  )}
                />
              </TableCell>
            </TableRow>
            {fields &&
              fields.map((role, index) => (
                <TableRow key={role.id}>
                  <TableCell>{role.name}</TableCell>
                  <TableCell>{role.description}</TableCell>
                  <TableCell>
                    <Controller
                      control={control}
                      name={`roles.${index}.currentPermission`}
                      defaultValue={djangoContext?.aclTypes.nothing.value}
                      render={({ field }) => (
                        <Select
                          {...field}
                          fullWidth={true}
                          disabled={watch("isPublic")}
                          MenuProps={{ disableScrollLock: true }}
                        >
                          <MenuItem value={0}>(未設定)</MenuItem>
                          {Object.keys(djangoContext?.aclTypes ?? {}).map(
                            (key, index) => (
                              <MenuItem
                                key={index}
                                value={djangoContext?.aclTypes[key].value}
                              >
                                {djangoContext?.aclTypes[key].name}
                              </MenuItem>
                            )
                          )}
                        </Select>
                      )}
                    />
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </Box>
    </Box>
  );
};
