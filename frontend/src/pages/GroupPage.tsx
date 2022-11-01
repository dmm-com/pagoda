import EastOutlinedIcon from "@mui/icons-material/EastOutlined";
import {
  Box,
  Button,
  Container,
  Divider,
  Grid,
  List,
  ListItem,
  Typography,
} from "@mui/material";
import React, { FC, useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { SearchBox } from "../components/common/SearchBox";
import { GroupImportModal } from "../components/group/GroupImportModal";
import { GroupTreeRoot } from "../components/group/GroupTreeRoot";

import { newGroupPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";

export const GroupPage: FC = () => {
  const [keyword, setKeyword] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState<number>();
  const [openImportModal, setOpenImportModal] = useState(false);

  const groupTrees = useAsync(async () => {
    return await aironeApiClientV2.getGroupTrees();
  });

  const usersInGroup = useAsync(async (): Promise<
    Array<{ id: number; username: string }>
  > => {
    if (selectedGroupId != null) {
      const group = await aironeApiClientV2.getGroup(selectedGroupId);
      return group.members.map((member) => ({
        id: member["id"],
        username: member["username"],
      }));
    } else {
      return [];
    }
  }, [selectedGroupId]);

  const filteredUsersInGroup = useMemo(() => {
    return (
      usersInGroup.value?.filter((user) => user.username.includes(keyword)) ??
      []
    );
  }, [usersInGroup, keyword]);

  const handleSelectGroupId = (groupId: number | null) => {
    setSelectedGroupId(groupId);
  };

  const handleExport = useCallback(async () => {
    await aironeApiClientV2.exportGroups("group.yaml");
  }, []);

  return (
    <Box display="flex" flexDirection="column" flexGrow="1">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">グループ管理</Typography>
      </AironeBreadcrumbs>

      <Container sx={{ marginTop: "111px" }}>
        <Box display="flex" justifyContent="space-between" sx={{ pb: "64px" }}>
          <Typography variant="h2">グループ管理</Typography>
          <Box display="flex" alignItems="flex-end">
            <Box display="flex" alignItems="center">
              <Box mx="8px">
                <Button
                  variant="contained"
                  color="info"
                  sx={{ margin: "0 4px" }}
                  onClick={handleExport}
                >
                  エクスポート
                </Button>
                <Button
                  variant="contained"
                  color="info"
                  sx={{ margin: "0 4px" }}
                  onClick={() => setOpenImportModal(true)}
                >
                  インポート
                </Button>
                <GroupImportModal
                  openImportModal={openImportModal}
                  closeImportModal={() => setOpenImportModal(false)}
                />
              </Box>
              <Button
                variant="contained"
                color="secondary"
                component={Link}
                to={newGroupPath()}
                sx={{ height: "48px", borderRadius: "24px" }}
              >
                <EastOutlinedIcon /> 新規グループを作成
              </Button>
            </Box>
          </Box>
        </Box>
      </Container>

      <Grid
        container
        flexGrow="1"
        columns={6}
        display="flex"
        sx={{ borderTop: 1, borderColor: "#0000008A" }}
      >
        <Grid item xs={1} />
        <Grid item xs={4} sx={{ p: "16px" }}>
          {groupTrees.loading ? (
            <Loading />
          ) : (
            <Box>
              <Typography mt="16px">
                選択したいグループにチェックマークを入れてください。
              </Typography>
              <Divider sx={{ mt: "16px" }} />
              <GroupTreeRoot
                groupTrees={groupTrees.value}
                selectedGroupId={selectedGroupId}
                handleSelectGroupId={handleSelectGroupId}
              />
            </Box>
          )}
        </Grid>
        <Grid
          item
          xs={1}
          sx={{ borderLeft: 1, borderColor: "#0000008A", p: "16px" }}
        >
          <Typography my="8px">
            属するユーザ(計 {usersInGroup.value?.length ?? 0})
          </Typography>
          <SearchBox
            placeholder="ユーザを絞り込む"
            value={keyword}
            onChange={(e) => {
              setKeyword(e.target.value);
            }}
          />
          <List>
            {filteredUsersInGroup.map((user, index) => (
              <Box key={user.id}>
                {index !== 0 && <Divider />}
                <ListItem>{user.username}</ListItem>
              </Box>
            ))}
          </List>
        </Grid>
      </Grid>
    </Box>
  );
};
