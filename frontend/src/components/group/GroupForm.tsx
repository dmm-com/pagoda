import { GroupMember } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Autocomplete,
  Box,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import React, { FC, useState } from "react";
import { Control, Controller, UseFormSetValue } from "react-hook-form";
import { useAsync } from "react-use";

import { filterAncestorsAndOthers } from "../../services/group/Edit";

import { GroupTreeRoot } from "./GroupTreeRoot";
import { Schema } from "./groupForm/GroupFormSchema";

import { Loading } from "components/common/Loading";
import { aironeApiClient } from "repository/AironeApiClient";

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  groupId?: number;
}

export const GroupForm: FC<Props> = ({ control, setValue, groupId }) => {
  const [userKeyword, setUserKeyword] = useState("");

  const users = useAsync(async () => {
    const _users = await aironeApiClient.getUsers(1, userKeyword);
    return _users.results?.map(
      (user): GroupMember => ({ id: user.id, username: user.username })
    );
  }, [userKeyword]);

  const groupTrees = useAsync(async () => {
    const _groupTrees = await aironeApiClient.getGroupTrees();
    return groupId != null
      ? filterAncestorsAndOthers(_groupTrees, groupId)
      : _groupTrees;
  });

  return (
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
            <TableCell>
              <Typography>グループ名</Typography>
            </TableCell>
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
                    placeholder="グループ名"
                    error={error != null}
                    helperText={error?.message}
                    sx={{ width: "100%" }}
                  />
                )}
              />
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography>登録ユーザ</Typography>
            </TableCell>
            <TableCell>
              <Controller
                name="members"
                control={control}
                defaultValue={[]}
                render={({ field }) => (
                  <Autocomplete
                    {...field}
                    options={users.value ?? []}
                    getOptionLabel={(option: GroupMember) => option.username}
                    isOptionEqualToValue={(option: GroupMember, value) =>
                      option.id === value.id
                    }
                    inputValue={userKeyword}
                    renderInput={(params) => (
                      <TextField {...params} variant="outlined" />
                    )}
                    onInputChange={(_e, value: string) => setUserKeyword(value)}
                    onChange={(_e, value: GroupMember[]) => {
                      setValue("members", value, {
                        shouldDirty: true,
                        shouldValidate: true,
                      });
                    }}
                    multiple
                  />
                )}
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
      <Box my="32px">
        <Typography variant="h4" align="center" my="16px">
          所属グループ
        </Typography>
        <Typography variant="h6" align="center" my="16px">
          直下となるグループにチェックマークを入れてください。独立グループの場合は未選択のまま保存してください。
        </Typography>
      </Box>
      <Divider sx={{ mt: "16px" }} />
      {groupTrees.loading ? (
        <Loading />
      ) : (
        <Controller
          name="parentGroup"
          control={control}
          render={({ field }) => (
            <GroupTreeRoot
              groupTrees={groupTrees.value ?? []}
              selectedGroupId={field.value ?? null}
              handleSelectGroupId={(groupId: number | null) =>
                setValue("parentGroup", groupId, {
                  shouldDirty: true,
                  shouldValidate: true,
                })
              }
            />
          )}
        />
      )}
    </Box>
  );
};
