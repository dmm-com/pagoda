import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import {
  Box,
  IconButton,
  List,
  ListItem,
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
import { Link, useNavigate } from "react-router-dom";

import { useAsyncWithThrow } from "../../hooks/useAsyncWithThrow";
import { aironeApiClient } from "../../repository/AironeApiClient";
import { Confirmable } from "../common/Confirmable";
import { Loading } from "../common/Loading";

import { rolePath, rolesPath, topPath } from "Routes";

const StyledList = styled(List)(() => ({
  padding: "0",
}));

const StyledListItem = styled(ListItem)(() => ({
  padding: "0",
}));

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  margin: theme.spacing(1),
})) as OverridableComponent<ExtendButtonBaseTypeMap<IconButtonTypeMap>>;

export const RoleList: FC = ({}) => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [toggle, setToggle] = useState(false);

  const roles = useAsyncWithThrow(async () => {
    return await aironeApiClient.getRoles();
  }, [toggle]);

  const handleDelete = async (roleId: number) => {
    try {
      await aironeApiClient.deleteRole(roleId);
      enqueueSnackbar(`ロールの削除が完了しました`, {
        variant: "success",
      });
      navigate(topPath(), { replace: true });
      navigate(rolesPath(), { replace: true });
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
        <Table data-testid="RoleList">
          <TableHead>
            <TableRow sx={{ backgroundColor: "#455A64" }}>
              <TableCell sx={{ color: "#FFFFFF" }}>ロール</TableCell>
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
                  <StyledList>
                    {role.users.map((user) => (
                      <StyledListItem key={user.id}>
                        <Typography ml="58px" my="4px">
                          {user.username}
                        </Typography>
                      </StyledListItem>
                    ))}
                    {role.groups.map((group) => (
                      <StyledListItem key={group.id}>
                        <Typography ml="58px" my="4px">
                          {group.name}
                        </Typography>
                      </StyledListItem>
                    ))}
                    {role.adminUsers.map((user) => (
                      <StyledListItem key={user.id}>
                        <Box display="flex" my="4px">
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
                      </StyledListItem>
                    ))}
                    {role.adminGroups.map((group) => (
                      <StyledListItem key={group.id}>
                        <Box display="flex" my="4px">
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
                      </StyledListItem>
                    ))}
                  </StyledList>
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
