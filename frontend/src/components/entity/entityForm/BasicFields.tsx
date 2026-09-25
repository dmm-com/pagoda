import {
  Autocomplete,
  Box,
  Checkbox,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TextField,
  Typography,
} from "@mui/material";
import { FC, useMemo } from "react";
import { Control, Controller, useWatch } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form";

import { Schema } from "./EntityFormSchema";

import {
  HeaderTableCell,
  HeaderTableRow,
  StyledTableRow,
} from "components/common/Table";
import { useTranslation } from "hooks/useTranslation";
import { fuzzyMatch } from "services/StringUtil";

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  referralEntities?: Array<{ id: number; name: string }>;
}

export const BasicFields: FC<Props> = ({
  control,
  referralEntities,
  setValue,
}) => {
  const { t } = useTranslation();
  const currItemNameType = useWatch({ control, name: "itemNameType" });
  const attrs = useWatch({
    control,
    name: "attrs",
    defaultValue: [],
  });

  const autoNamePreview = useMemo(() => {
    if (currItemNameType !== "AT") return "";
    return (attrs ?? [])
      .filter((attr) => Number(attr.nameOrder) > 0)
      .sort((a, b) => Number(a.nameOrder) - Number(b.nameOrder))
      .map((attr) => `${attr.namePrefix}${attr.name}${attr.namePostfix}`)
      .join("");
  }, [currItemNameType, attrs]);

  return (
    <Box>
      <Typography variant="h4" align="center" my="16px">
        {t("entity.form.basicInfoTitle")}
      </Typography>

      <Table className="table table-bordered">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell width="400px">
              {t("entity.form.itemHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="800px">
              {t("entity.form.valueHeader")}
            </HeaderTableCell>
          </HeaderTableRow>
        </TableHead>
        <TableBody>
          <StyledTableRow>
            <TableCell>{t("entity.form.nameLabel")}</TableCell>
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
                    placeholder={t("entity.form.nameLabel")}
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
            <TableCell>{t("entity.form.noteLabel")}</TableCell>
            <TableCell>
              <Controller
                name="note"
                control={control}
                defaultValue=""
                render={({ field, fieldState: { error } }) => (
                  <TextField
                    {...field}
                    required
                    placeholder={t("entity.form.noteLabel")}
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
            <TableCell>{t("entity.form.itemNameTypeLabel")}</TableCell>
            <TableCell>
              <Controller
                name="itemNameType"
                control={control}
                defaultValue="US"
                render={({ field }) => (
                  <Select
                    {...field}
                    id="itemNameType"
                    inputProps={{
                      "aria-label": t("entity.form.itemNameTypeLabel"),
                    }}
                    size="small"
                    sx={{ minWidth: "300px" }}
                  >
                    <MenuItem value={"US"}>
                      {t("entity.form.itemNameTypeUser")}
                    </MenuItem>
                    <MenuItem value={"ID"}>
                      {t("entity.form.itemNameTypeUuid")}
                    </MenuItem>
                    <MenuItem value={"AT"}>
                      {t("entity.form.itemNameTypeAttr")}
                    </MenuItem>
                  </Select>
                )}
              />
              {currItemNameType === "AT" && (
                <Typography
                  variant="body2"
                  sx={{
                    mt: 1,
                    color: autoNamePreview ? "text.primary" : "text.disabled",
                  }}
                >
                  {autoNamePreview || t("entity.form.autoNameEmptyPreview")}
                </Typography>
              )}
            </TableCell>
          </StyledTableRow>
          <StyledTableRow>
            <TableCell
              sx={{
                color:
                  currItemNameType !== "US" ? "text.disabled" : "text.primary",
              }}
            >
              {t("entity.form.itemNamePatternLabel")}
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
                      placeholder={t("entity.form.itemNamePatternLabel")}
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
            <TableCell>{t("entity.form.showOnTopPage")}</TableCell>
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
          <StyledTableRow>
            <TableCell>{t("entity.form.deleteChainExcludeLabel")}</TableCell>
            <TableCell>
              <Controller
                name="deleteChainExcludeEntities"
                control={control}
                defaultValue={[]}
                render={({ field }) => (
                  <Autocomplete
                    {...field}
                    multiple
                    options={referralEntities ?? []}
                    getOptionLabel={(option: { id: number; name: string }) =>
                      option.name
                    }
                    filterOptions={(options, state) =>
                      options.filter((option) =>
                        fuzzyMatch(option.name, state.inputValue),
                      )
                    }
                    isOptionEqualToValue={(
                      option: { id: number; name: string },
                      value: { id: number; name: string },
                    ) => option.id === value.id}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        variant="outlined"
                        placeholder={t("entity.form.selectEntityPlaceholder")}
                      />
                    )}
                    onChange={(
                      _e,
                      value: Array<{ id: number; name: string }>,
                    ) =>
                      setValue("deleteChainExcludeEntities", value, {
                        shouldDirty: true,
                        shouldValidate: true,
                      })
                    }
                    size="small"
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
