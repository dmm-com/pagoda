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
import React, { FC, useState } from "react";
import {
  Control,
  Controller,
  FieldError,
  UseFormSetValue,
} from "react-hook-form";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../../repository/AironeApiClientV2";

import { Schema } from "./roleForm/RoleFormSchema";

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
}

export const RoleForm: FC<Props> = ({ control, setValue }) => {
  const [userKeyword, setUserKeyword] = useState("");
  const [adminUserKeyword, setAdminUserKeyword] = useState("");
  const [groupUserKeyword, setGroupUserKeyword] = useState("");
  const [adminGroupUserKeyword, setGroupAdminUserKeyword] = useState("");

  // TODO implement pagination and incremental search
  const adminGroups = useAsync(async () => {
    const _groups = await aironeApiClientV2.getGroups(1, adminGroupUserKeyword);
    return _groups.results?.map(
      (group): RoleGroup => ({ id: group.id, name: group.name }),
    );
  }, [adminGroupUserKeyword]);
  const groups = useAsync(async () => {
    const _groups = await aironeApiClientV2.getGroups(1, groupUserKeyword);
    return _groups.results?.map(
      (group): RoleGroup => ({ id: group.id, name: group.name }),
    );
  }, [groupUserKeyword]);
  const adminUsers = useAsync(async () => {
    const _users = await aironeApiClientV2.getUsers(1, adminUserKeyword);
    return _users.results?.map(
      (user): RoleUser => ({ id: user.id, username: user.username }),
    );
  }, [adminUserKeyword]);
  const users = useAsync(async () => {
    const _users = await aironeApiClientV2.getUsers(1, userKeyword);
    return _users.results?.map(
      (user): RoleUser => ({ id: user.id, username: user.username }),
    );
  }, [userKeyword]);

  return (
    <Box>
      <Box>
        <Table className="table table-bordered">
          <TableHead>
            <TableRow sx={{ backgroundColor: "#455A64" }}>
              <TableCell sx={{ color: "#FFFFFF" }}>項目</TableCell>
              <TableCell sx={{ color: "#FFFFFF" }}>内容</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell>ロール名</TableCell>
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
                      placeholder="ロール名"
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
                  name="description"
                  control={control}
                  defaultValue=""
                  render={({ field }) => (
                    <TextField
                      variant="standard"
                      placeholder="備考"
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
            ユーザ/グループを登録
          </Typography>
          <Typography variant="h6" align="center" my="16px">
            ロール管理するグループまたはユーザを登録してください。
          </Typography>
        </Box>

        <Box my="64px">
          <Typography align="left" my="8px">
            グループ登録
          </Typography>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: "#455A64" }}>
                <TableCell sx={{ color: "#FFFFFF" }}>項目</TableCell>
                <TableCell sx={{ color: "#FFFFFF" }}>内容</TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>管理者</TableCell>
                <TableCell>
                  <Controller
                    name="adminGroups"
                    control={control}
                    defaultValue={[]}
                    render={({ field, fieldState: { error } }) => (
                      <Autocomplete
                        {...field}
                        options={adminGroups.value ?? []}
                        getOptionLabel={(option: RoleGroup) => option.name}
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
                <TableCell>メンバー</TableCell>
                <TableCell>
                  <Controller
                    name="groups"
                    control={control}
                    defaultValue={[]}
                    render={({ field, fieldState: { error } }) => (
                      <Autocomplete
                        {...field}
                        options={groups.value ?? []}
                        getOptionLabel={(option: RoleGroup) => option.name}
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
            ユーザ登録
          </Typography>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: "#455A64" }}>
                <TableCell sx={{ color: "#FFFFFF" }}>項目</TableCell>
                <TableCell sx={{ color: "#FFFFFF" }}>内容</TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>管理者</TableCell>
                <TableCell>
                  <Controller
                    name="adminUsers"
                    control={control}
                    defaultValue={[]}
                    render={({ field, fieldState: { error } }) => (
                      <Autocomplete
                        {...field}
                        options={adminUsers.value ?? []}
                        getOptionLabel={(option: RoleUser) => option.username}
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
                <TableCell>メンバー</TableCell>
                <TableCell>
                  <Controller
                    name="users"
                    control={control}
                    defaultValue={[]}
                    render={({ field, fieldState: { error } }) => (
                      <Autocomplete
                        {...field}
                        options={users.value ?? []}
                        getOptionLabel={(option: RoleUser) => option.username}
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
