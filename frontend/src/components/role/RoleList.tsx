import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import {
  Box,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { ExtendButtonBaseTypeMap } from "@mui/material/ButtonBase/ButtonBase";
import { IconButtonTypeMap } from "@mui/material/IconButton/IconButton";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { Link, useHistory } from "react-router-dom";

import { useAsyncWithThrow } from "../../hooks/useAsyncWithThrow";
import { aironeApiClientV2 } from "../../repository/AironeApiClientV2";
import { Confirmable } from "../common/Confirmable";
import { Loading } from "../common/Loading";

import { rolePath, rolesPath, topPath } from "Routes";

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  margin: theme.spacing(1),
})) as OverridableComponent<ExtendButtonBaseTypeMap<IconButtonTypeMap>>;

export const RoleList: FC = ({}) => {
  const history = useHistory();
  const { enqueueSnackbar } = useSnackbar();
  const [toggle, setToggle] = useState(false);

  const roles = useAsyncWithThrow(async () => {
    return await aironeApiClientV2.getRoles();
  }, [toggle]);

  const handleDelete = async (roleId: number) => {
    try {
      await aironeApiClientV2.deleteRole(roleId);
      enqueueSnackbar(`ロールの削除が完了しました`, {
        variant: "success",
      });
      history.replace(topPath());
      history.replace(rolesPath());
      setToggle(!toggle);
    } catch (e) {
      enqueueSnackbar("ロールの削除が失敗しました", {
        variant: "error",
      });
    }
  };

  return (
    <Box>
      {roles.loading ? (
        <Loading />
      ) : (
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: "#455A64" }}>
              <TableCell sx={{ color: "#FFFFFF" }}>項目</TableCell>
              <TableCell sx={{ color: "#FFFFFF" }}>備考</TableCell>
              <TableCell sx={{ color: "#FFFFFF" }}>
                登録ユーザ・グループ
              </TableCell>
              <TableCell sx={{ color: "#FFFFFF" }}>削除</TableCell>
              <TableCell sx={{ color: "#FFFFFF" }}>編集</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {roles.value?.map((role) => (
              <TableRow key={role.id}>
                <TableCell>{role.name}</TableCell>
                <TableCell>{role.description}</TableCell>
                <TableCell>
                  <>
                    {role.users.map((user) => (
                      <Typography key={user.id} ml="58px" my="4px">
                        {user.username}
                      </Typography>
                    ))}
                    {role.groups.map((group) => (
                      <Typography key={group.id} ml="58px" my="4px">
                        {group.name}
                      </Typography>
                    ))}
                    {role.adminUsers.map((user) => (
                      <Box key={user.id} display="flex" my="4px">
                        <Box
                          display="flex"
                          alignItems="center"
                          p="4px"
                          mx="4px"
                          sx={{
                            color: "white",
                            backgroundColor: "#0000008A",
                            borderRadius: "12px",
                          }}
                        >
                          管理者
                        </Box>
                        <Typography>{user.username}</Typography>
                      </Box>
                    ))}
                    {role.adminGroups.map((group) => (
                      <Box key={group.id} display="flex" my="4px">
                        <Box
                          display="flex"
                          alignItems="center"
                          p="4px"
                          mx="4px"
                          sx={{
                            color: "white",
                            backgroundColor: "#0000008A",
                            borderRadius: "12px",
                          }}
                        >
                          管理者
                        </Box>
                        <Typography>{group.name}</Typography>
                      </Box>
                    ))}
                  </>
                </TableCell>
                <TableCell>
                  <Confirmable
                    componentGenerator={(handleOpen) => (
                      <StyledIconButton
                        disabled={!role.isEditable}
                        onClick={handleOpen}
                      >
                        <DeleteOutlineIcon />
                      </StyledIconButton>
                    )}
                    dialogTitle="本当に削除しますか？"
                    onClickYes={() => handleDelete(role.id)}
                  />
                </TableCell>
                <TableCell>
                  <StyledIconButton
                    disabled={!role.isEditable}
                    component={Link}
                    to={rolePath(role.id)}
                  >
                    <EditOutlinedIcon />
                  </StyledIconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Box>
  );
};
