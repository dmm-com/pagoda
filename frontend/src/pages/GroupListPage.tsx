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
import { FC, Suspense, useCallback, useMemo, useState } from "react";
import { Link } from "react-router";

import { GroupControlMenu } from "../components/group/GroupControlMenu";
import { GroupImportModal } from "../components/group/GroupImportModal";
import { GroupTreeRoot } from "../components/group/GroupTreeRoot";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SearchBox } from "components/common/SearchBox";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import { newGroupPath, topPath } from "routes/Routes";
import { TITLE_TEMPLATES } from "services";
import { ServerContext } from "services/ServerContext";
import { fuzzyMatch } from "services/StringUtil";

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

const GroupListContent: FC = () => {
  const { t } = useTranslation();
  const [keyword, setKeyword] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [groupAnchorEls, setGroupAnchorEls] = useState<{
    groupId: number;
    el: HTMLButtonElement;
  } | null>();

  const { data: groupTrees, mutate: refreshGroupTrees } = usePagodaSWR(
    ["groupTrees"],
    () => aironeApiClient.getGroupTrees(),
    { suspense: true },
  );

  const { data: usersInGroup } = usePagodaSWR(
    selectedGroupId != null ? ["group", selectedGroupId] : null,
    async () => {
      const group = await aironeApiClient.getGroup(selectedGroupId!);
      return group.members.map((member) => ({
        id: member.id,
        username: member.username,
      }));
    },
  );

  const filteredUsersInGroup = useMemo(() => {
    return (
      usersInGroup?.filter((user) => fuzzyMatch(user.username, keyword)) ?? []
    );
  }, [usersInGroup, keyword]);

  const handleSelectGroupId = (groupId: number | null) => {
    setSelectedGroupId(groupId);
  };

  return (
    <Box
      display="flex"
      flexDirection={{ xs: "column", md: "row" }}
      flexGrow={1}
      gap={2}
      paddingBottom={4}
    >
      <Box flex={1}>
        <StyledContainer>
          <Typography>{t("group.list.selectHelp")}</Typography>
          <Divider sx={{ mt: "16px" }} />
          <GroupTreeRoot
            groupTrees={groupTrees}
            selectedGroupId={selectedGroupId}
            handleSelectGroupId={handleSelectGroupId}
            setGroupAnchorEls={setGroupAnchorEls}
          />
          {groupAnchorEls != null && (
            <GroupControlMenu
              groupId={groupAnchorEls.groupId}
              anchorElem={groupAnchorEls.el}
              handleClose={() => setGroupAnchorEls(null)}
              setToggle={() => refreshGroupTrees()}
            />
          )}
        </StyledContainer>
      </Box>

      <UserListPanel>
        <Typography>
          {t("group.list.memberCount", {
            count: usersInGroup?.length ?? 0,
          })}
        </Typography>
        <SearchBox
          placeholder={t("group.list.searchPlaceholder")}
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
  );
};

export const GroupListPage: FC = () => {
  const { t } = useTranslation();
  const [openImportModal, setOpenImportModal] = useState(false);

  const handleExport = useCallback(async () => {
    await aironeApiClient.exportGroups("group.yaml");
  }, []);

  const isSuperuser = ServerContext.getInstance()?.user?.isSuperuser ?? false;
  const isReadonly = ServerContext.getInstance()?.user?.isReadonly ?? false;

  usePageTitle(TITLE_TEMPLATES.groupList);

  return (
    <Box display="flex" flexDirection="column" flexGrow="1">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">{t("group.list.pageTitle")}</Typography>
      </AironeBreadcrumbs>

      <PageHeader title={t("group.list.pageTitle")}>
        <Button
          variant="contained"
          color="info"
          sx={{ margin: "0 4px" }}
          onClick={handleExport}
        >
          {t("common.export")}
        </Button>
        <Button
          variant="contained"
          color="info"
          sx={{ margin: "0 4px" }}
          onClick={() => setOpenImportModal(true)}
          disabled={isReadonly}
        >
          {t("common.import")}
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
          <AddIcon /> {t("group.list.createNew")}
        </Button>
      </PageHeader>

      <Suspense fallback={<Loading />}>
        <GroupListContent />
      </Suspense>
    </Box>
  );
};
