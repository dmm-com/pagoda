import {
  RoleGroup,
  RoleUser,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Autocomplete,
  Box,
  Chip,
  FormHelperText,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { FC, useState } from "react";
import {
  Control,
  Controller,
  FieldError,
  UseFormSetValue,
} from "react-hook-form";

import { usePagodaSWR } from "../../hooks/usePagodaSWR";
import { useTranslation } from "../../hooks/useTranslation";
import { aironeApiClient } from "../../repository/AironeApiClient";

import { Schema } from "./roleForm/RoleFormSchema";

import { fuzzyMatch } from "services/StringUtil";

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
}

export const RoleForm: FC<Props> = ({ control, setValue }) => {
  const { t } = useTranslation();
  const [userKeyword, setUserKeyword] = useState("");
  const [adminUserKeyword, setAdminUserKeyword] = useState("");
  const [groupUserKeyword, setGroupUserKeyword] = useState("");
  const [adminGroupUserKeyword, setGroupAdminUserKeyword] = useState("");

  // TODO implement pagination and incremental search
  const { data: adminGroups } = usePagodaSWR(
    ["groups", 1, adminGroupUserKeyword],
    async () => {
      const _groups = await aironeApiClient.getGroups(1, adminGroupUserKeyword);
      return _groups.results?.map(
        (group): RoleGroup => ({ id: group.id, name: group.name }),
      );
    },
  );
  const { data: groups } = usePagodaSWR(
    ["groups", 1, groupUserKeyword],
    async () => {
      const _groups = await aironeApiClient.getGroups(1, groupUserKeyword);
      return _groups.results?.map(
        (group): RoleGroup => ({ id: group.id, name: group.name }),
      );
    },
  );
  const { data: adminUsers } = usePagodaSWR(
    ["users", 1, adminUserKeyword],
    async () => {
      const _users = await aironeApiClient.getUsers(1, adminUserKeyword);
      return _users.results?.map(
        (user): RoleUser => ({ id: user.id, username: user.username }),
      );
    },
  );
  const { data: users } = usePagodaSWR(["users", 1, userKeyword], async () => {
    const _users = await aironeApiClient.getUsers(1, userKeyword);
    return _users.results?.map(
      (user): RoleUser => ({ id: user.id, username: user.username }),
    );
  });

  return (
    <Box>
      <Box>
        <Table className="table table-bordered" data-testid="basic">
          <TableHead>
            <TableRow sx={{ backgroundColor: "#455A64" }}>
              <TableCell sx={{ color: "#FFFFFF" }}>
                {t("role.form.columnItem")}
              </TableCell>
              <TableCell sx={{ color: "#FFFFFF" }}>
                {t("role.form.columnContent")}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell>{t("role.form.name")}</TableCell>
              <TableCell>
                <Controller
                  name="name"
                  control={control}
                  defaultValue=""
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      variant="standard"
                      required
                      placeholder={t("role.form.namePlaceholder")}
                      error={error != null}
                      helperText={error?.message}
                      sx={{ width: "100%" }}
                      inputProps={{ "data-1p-ignore": true }}
                    />
                  )}
                />
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>{t("role.form.description")}</TableCell>
              <TableCell>
                <Controller
                  name="description"
                  control={control}
                  defaultValue=""
                  render={({ field }) => (
                    <TextField
                      variant="standard"
                      placeholder={t("role.form.descriptionPlaceholder")}
                      {...field}
                      sx={{ width: "100%" }}
                    />
                  )}
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </Box>

      <Box mt="64px">
        <Box my="32px">
          <Typography variant="h4" align="center" my="16px">
            {t("role.form.registerSectionTitle")}
          </Typography>
          <Typography variant="h6" align="center" my="16px">
            {t("role.form.registerSectionHelp")}
          </Typography>
        </Box>

        <Box my="64px">
          <Typography align="left" my="8px">
            {t("role.form.groupRegisterTitle")}
          </Typography>
          <Table data-testid="group">
            <TableHead>
              <TableRow sx={{ backgroundColor: "#455A64" }}>
                <TableCell sx={{ color: "#FFFFFF" }}>
                  {t("role.form.columnItem")}
                </TableCell>
                <TableCell sx={{ color: "#FFFFFF" }}>
                  {t("role.form.columnContent")}
                </TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>{t("role.form.admin")}</TableCell>
                <TableCell>
                  <Controller
                    name="adminGroups"
                    control={control}
                    defaultValue={[]}
                    render={({ field, fieldState: { error } }) => (
                      <Autocomplete
                        {...field}
                        options={adminGroups ?? []}
                        getOptionLabel={(option: RoleGroup) => option.name}
                        filterOptions={(options, state) =>
                          options.filter((option) =>
                            fuzzyMatch(option.name, state.inputValue),
                          )
                        }
                        isOptionEqualToValue={(option, value) =>
                          option.id === value.id
                        }
                        inputValue={adminGroupUserKeyword}
                        renderInput={(params) => (
                          <Box>
                            <TextField {...params} variant="outlined" />
                            {/* NOTE: role schema will inject some nested errors. It shows the first. */}
                            {Array.isArray(error) && (
                              <>
                                {(() => {
                                  const first = (error as FieldError[]).filter(
                                    (e) => e.message != null,
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
                        renderTags={(value, getTagProps) =>
                          value.map((option, index) => (
                            <Chip
                              {...getTagProps({ index })}
                              key={option.name}
                              label={option.name}
                              color={
                                (error as FieldError[] | undefined)?.[index]
                                  ? "error"
                                  : undefined
                              }
                            />
                          ))
                        }
                        onChange={(_e, value: RoleGroup[]) =>
                          setValue("adminGroups", value, {
                            shouldDirty: true,
                            shouldValidate: true,
                          })
                        }
                        onInputChange={(_e, value: string) =>
                          setGroupAdminUserKeyword(value)
                        }
                        multiple
                      />
                    )}
                  />
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>{t("role.form.member")}</TableCell>
                <TableCell>
                  <Controller
                    name="groups"
                    control={control}
                    defaultValue={[]}
                    render={({ field, fieldState: { error } }) => (
                      <Autocomplete
                        {...field}
                        options={groups ?? []}
                        getOptionLabel={(option: RoleGroup) => option.name}
                        filterOptions={(options, state) =>
                          options.filter((option) =>
                            fuzzyMatch(option.name, state.inputValue),
                          )
                        }
                        isOptionEqualToValue={(option, value) =>
                          option.id === value.id
                        }
                        inputValue={groupUserKeyword}
                        renderInput={(params) => (
                          <Box>
                            <TextField {...params} variant="outlined" />
                            {/* NOTE: role schema will inject some nested errors. It shows the first. */}
                            {Array.isArray(error) && (
                              <>
                                {(() => {
                                  const first = (error as FieldError[]).filter(
                                    (e) => e.message != null,
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
                        renderTags={(value, getTagProps) =>
                          value.map((option, index) => (
                            <Chip
                              {...getTagProps({ index })}
                              key={option.name}
                              label={option.name}
                              color={
                                (error as FieldError[] | undefined)?.[index]
                                  ? "error"
                                  : undefined
                              }
                            />
                          ))
                        }
                        onChange={(_e, value: RoleGroup[]) =>
                          setValue("groups", value, {
                            shouldDirty: true,
                            shouldValidate: true,
                          })
                        }
                        onInputChange={(_e, value: string) =>
                          setGroupUserKeyword(value)
                        }
                        multiple
                      />
                    )}
                  />
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Box>

        <Box my="64px">
          <Typography align="left" my="8px">
            {t("role.form.userRegisterTitle")}
          </Typography>
          <Table data-testid="user">
            <TableHead>
              <TableRow sx={{ backgroundColor: "#455A64" }}>
                <TableCell sx={{ color: "#FFFFFF" }}>
                  {t("role.form.columnItem")}
                </TableCell>
                <TableCell sx={{ color: "#FFFFFF" }}>
                  {t("role.form.columnContent")}
                </TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>{t("role.form.admin")}</TableCell>
                <TableCell>
                  <Controller
                    name="adminUsers"
                    control={control}
                    defaultValue={[]}
                    render={({ field, fieldState: { error } }) => (
                      <Autocomplete
                        {...field}
                        options={adminUsers ?? []}
                        getOptionLabel={(option: RoleUser) => option.username}
                        filterOptions={(options, state) =>
                          options.filter((option) =>
                            fuzzyMatch(option.username, state.inputValue),
                          )
                        }
                        isOptionEqualToValue={(option, value) =>
                          option.id === value.id
                        }
                        inputValue={adminUserKeyword}
                        renderInput={(params) => (
                          <Box>
                            <TextField {...params} variant="outlined" />
                            {/* NOTE: role schema will inject some nested errors. It shows the first. */}
                            {Array.isArray(error) && (
                              <>
                                {(() => {
                                  const first = (error as FieldError[]).filter(
                                    (e) => e.message != null,
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
                        renderTags={(value, getTagProps) =>
                          value.map((option, index) => (
                            <Chip
                              {...getTagProps({ index })}
                              key={option.username}
                              label={option.username}
                              color={
                                (error as FieldError[] | undefined)?.[index]
                                  ? "error"
                                  : undefined
                              }
                            />
                          ))
                        }
                        onChange={(_e, value: RoleUser[]) =>
                          setValue("adminUsers", value, {
                            shouldDirty: true,
                            shouldValidate: true,
                          })
                        }
                        onInputChange={(_e, value: string) =>
                          setAdminUserKeyword(value)
                        }
                        multiple
                      />
                    )}
                  />
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>{t("role.form.member")}</TableCell>
                <TableCell>
                  <Controller
                    name="users"
                    control={control}
                    defaultValue={[]}
                    render={({ field, fieldState: { error } }) => (
                      <Autocomplete
                        {...field}
                        options={users ?? []}
                        getOptionLabel={(option: RoleUser) => option.username}
                        filterOptions={(options, state) =>
                          options.filter((option) =>
                            fuzzyMatch(option.username, state.inputValue),
                          )
                        }
                        isOptionEqualToValue={(option, value) =>
                          option.id === value.id
                        }
                        inputValue={userKeyword}
                        renderInput={(params) => (
                          <Box>
                            <TextField {...params} variant="outlined" />
                            {/* NOTE: role schema will inject some nested errors. It shows the first. */}
                            {Array.isArray(error) && (
                              <>
                                {(() => {
                                  const first = (error as FieldError[]).filter(
                                    (e) => e.message != null,
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
                        renderTags={(value, getTagProps) =>
                          value.map((option, index) => (
                            <Chip
                              {...getTagProps({ index })}
                              key={option.username}
                              label={option.username}
                              color={
                                (error as FieldError[] | undefined)?.[index]
                                  ? "error"
                                  : undefined
                              }
                            />
                          ))
                        }
                        onChange={(_e, value: RoleUser[]) =>
                          setValue("users", value, {
                            shouldDirty: true,
                            shouldValidate: true,
                          })
                        }
                        onInputChange={(_e, value: string) =>
                          setUserKeyword(value)
                        }
                        multiple
                      />
                    )}
                  />
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Box>
      </Box>
    </Box>
  );
};
