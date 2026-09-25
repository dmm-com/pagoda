import {
  Box,
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
import { FC } from "react";
import { Control, Controller, useFieldArray } from "react-hook-form";
import { UseFormWatch } from "react-hook-form";

import { Schema } from "components/acl/aclForm/ACLFormSchema";
import { useTranslation } from "hooks/useTranslation";
import { ACLType, ACLTypeLabels } from "services/ACLUtil";

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

const StyledTableBody = styled(TableBody)({
  "tr:nth-of-type(odd)": {
    backgroundColor: "white",
  },
  "tr:nth-of-type(even)": {
    backgroundColor: "#607D8B0A",
  },
  "& td": {
    padding: "8px 16px",
  },
});

export const ACLForm: FC<Props> = ({ control, watch }) => {
  const { t } = useTranslation();

  const { fields } = useFieldArray({
    control,
    name: "roles",
  });

  return (
    <Box>
      <Table className="table table-bordered">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCellItem>{t("acl.form.item")}</HeaderTableCellItem>
            <HeaderTableCellContext>
              {t("acl.form.content")}
            </HeaderTableCellContext>
          </HeaderTableRow>
        </TableHead>
        <StyledTableBody>
          <TableRow>
            <TableCell>{t("acl.form.isPublicLabel")}</TableCell>
            <TableCell>
              <Controller
                name="isPublic"
                control={control}
                defaultValue={true}
                render={({ field }) => (
                  <Select
                    {...field}
                    id="is_public"
                    size="small"
                    fullWidth
                    value={field.value ? 1 : 0}
                    onChange={(e) => field.onChange(e.target.value === 1)}
                  >
                    <MenuItem value={1}>{t("acl.form.public")}</MenuItem>
                    <MenuItem value={0}>{t("acl.form.limitedPublic")}</MenuItem>
                  </Select>
                )}
              />
            </TableCell>
          </TableRow>
        </StyledTableBody>
      </Table>

      <Box>
        <Box my="32px">
          <Typography variant="h4" align="center">
            {t("acl.form.title")}
          </Typography>
        </Box>

        <Table id="table_role_list" className="table table-bordered">
          <TableHead>
            <HeaderTableRow>
              <HeaderTableCellItem>{t("acl.form.role")}</HeaderTableCellItem>
              <HeaderTableCellNote>{t("acl.form.note")}</HeaderTableCellNote>
              <HeaderTableCellContext />
            </HeaderTableRow>
          </TableHead>
          <StyledTableBody>
            <TableRow>
              <TableCell>{t("acl.form.everyone")}</TableCell>
              <TableCell />
              <TableCell>
                <Controller
                  control={control}
                  name="defaultPermission"
                  defaultValue={ACLType.Nothing}
                  render={({ field }) => (
                    <Select
                      {...field}
                      size="small"
                      fullWidth
                      disabled={watch("isPublic")}
                    >
                      {Object.values(ACLType).map((value) => (
                        <MenuItem key={value} value={value}>
                          {ACLTypeLabels[value]}
                        </MenuItem>
                      ))}
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
                      defaultValue={ACLType.Nothing}
                      render={({ field }) => (
                        <Select
                          {...field}
                          size="small"
                          fullWidth
                          disabled={watch("isPublic")}
                        >
                          {Object.values(ACLType).map((value) => (
                            <MenuItem key={value} value={value}>
                              {ACLTypeLabels[value]}
                            </MenuItem>
                          ))}
                        </Select>
                      )}
                    />
                  </TableCell>
                </TableRow>
              ))}
          </StyledTableBody>
        </Table>
      </Box>
    </Box>
  );
};
