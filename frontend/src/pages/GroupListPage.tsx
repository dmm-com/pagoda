import AddIcon from "@mui/icons-material/Add";
import {
  Box,
  Button,
  Container,
  Divider,
  List,
  ListItem,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useCallback, useMemo, useState } from "react";
import { Link } from "react-router";

import { SearchBox } from "../components/common/SearchBox";
import { GroupControlMenu } from "../components/group/GroupControlMenu";
import { GroupImportModal } from "../components/group/GroupImportModal";
import { GroupTreeRoot } from "../components/group/GroupTreeRoot";
import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { aironeApiClient } from "repository/AironeApiClient";
import { newGroupPath, topPath } from "routes/Routes";
import { ServerContext } from "services/ServerContext";

const StyledContainer = styled(Container)({
  paddingTop: "16px",
});

const UserListPanel = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  [theme.breakpoints.up("md")]: {
    width: "30%",
    borderLeft: "1px solid rgba(0, 0, 0, 0.12)",
  },
  [theme.breakpoints.down("md")]: {
    width: "100%",
    marginTop: theme.spacing(2),
  },
}));

export const GroupListPage: FC = () => {
  const [keyword, setKeyword] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [openImportModal, setOpenImportModal] = useState(false);
  const [groupAnchorEls, setGroupAnchorEls] = useState<{
    groupId: number;
    el: HTMLButtonElement;
  } | null>();
  const [toggle, setToggle] = useState(false);

  const groupTrees = useAsyncWithThrow(async () => {
    return await aironeApiClient.getGroupTrees();
  }, [toggle]);

  const usersInGroup = useAsyncWithThrow(async (): Promise<
    Array<{ id: number; username: string }>
  > => {
    if (selectedGroupId != null) {
      const group = await aironeApiClient.getGroup(selectedGroupId);
      return group.members.map((member) => ({
        id: member.id,
        username: member.username,
      }));
    } else {
      return [];
    }
  }, [selectedGroupId]);

  const filteredUsersInGroup = useMemo(() => {
    const keywordLower = keyword.toLowerCase();
    return (
      usersInGroup.value?.filter((user) =>
        user.username.toLowerCase().includes(keywordLower),
      ) ?? []
    );
  }, [usersInGroup, keyword]);

  const handleSelectGroupId = (groupId: number | null) => {
    setSelectedGroupId(groupId);
  };

  const handleExport = useCallback(async () => {
    await aironeApiClient.exportGroups("group.yaml");
  }, []);

  const isSuperuser = ServerContext.getInstance()?.user?.isSuperuser ?? false;

  return (
    <Box display="flex" flexDirection="column" flexGrow="1">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">グループ管理</Typography>
      </AironeBreadcrumbs>

      <PageHeader title="グループ管理">
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
        <Button
          variant="contained"
          color="secondary"
          disabled={!isSuperuser}
          component={Link}
          to={newGroupPath()}
          sx={{ height: "48px", borderRadius: "24px", ml: "16px" }}
        >
          <AddIcon /> 新規グループを作成
        </Button>
      </PageHeader>

      {groupTrees.loading ? (
        <Loading />
      ) : (
        <Box
          display="flex"
          flexDirection={{ xs: "column", md: "row" }}
          flexGrow={1}
          gap={2}
          paddingBottom={4}
        >
          <Box flex={1}>
            <StyledContainer>
              <Typography>
                選択したいグループにチェックマークを入れてください。
              </Typography>
              <Divider sx={{ mt: "16px" }} />
              <GroupTreeRoot
                groupTrees={groupTrees.value ?? []}
                selectedGroupId={selectedGroupId}
                handleSelectGroupId={handleSelectGroupId}
                setGroupAnchorEls={setGroupAnchorEls}
              />
              {groupAnchorEls != null && (
                <GroupControlMenu
                  groupId={groupAnchorEls.groupId}
                  anchorElem={groupAnchorEls.el}
                  handleClose={() => setGroupAnchorEls(null)}
                  setToggle={() => setToggle(!toggle)}
                />
              )}
            </StyledContainer>
          </Box>

          <UserListPanel>
            <Typography>
              属するユーザ(計 {usersInGroup.value?.length ?? 0})
            </Typography>
            <SearchBox
              placeholder="ユーザを絞り込む"
              value={keyword}
              onChange={(e) => {
                setKeyword(e.target.value);
              }}
            />
            <List data-testid="GroupMember">
              {filteredUsersInGroup.map((user, index) => (
                <Box key={user.id}>
                  {index !== 0 && <Divider />}
                  <ListItem>{user.username}</ListItem>
                </Box>
              ))}
            </List>
          </UserListPanel>
        </Box>
      )}
    </Box>
  );
};
