import { ACLObjtypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, Suspense, useState } from "react";
import { preload } from "swr";

import { usePagodaSWR, wrapFetcher } from "../hooks/usePagodaSWR";

import { ACLHistoryList } from "components/acl/ACLHistoryList";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntityControlMenu } from "components/entity/EntityControlMenu";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";

const MenuBox = styled(Box)(({}) => ({
  width: "50px",
}));

const ACLHistoryContent: FC<{ objectId: number }> = ({ objectId }) => {
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = useState(false);

  const { data: acl } = usePagodaSWR(
    ["acl", objectId],
    () => aironeApiClient.getAcl(objectId),
    { suspense: true },
  );

  const { data: aclHistory } = usePagodaSWR(
    ["aclHistory", objectId],
    () => aironeApiClient.getAclHistory(objectId),
    { suspense: true },
  );

  // One-shot page context (breadcrumbs / control menu); no need to track
  // server freshness on window focus.
  const { data: entityDetail } = usePagodaSWR(
    acl.objtype === ACLObjtypeEnum.Entity ? ["entity", objectId] : null,
    () => aironeApiClient.getEntity(objectId),
    { revalidateOnFocus: false },
  );

  const { data: entryRetrieve } = usePagodaSWR(
    acl.objtype === ACLObjtypeEnum.Entry ? ["entry", objectId] : null,
    () => aironeApiClient.getEntry(objectId),
    { revalidateOnFocus: false },
  );

  // Derived from fetched data; no state needed.
  const breadcrumbs = (() => {
    switch (acl.objtype) {
      case ACLObjtypeEnum.Entity:
        return entityDetail != null ? (
          <EntityBreadcrumbs entity={entityDetail} title="ACL変更履歴" />
        ) : (
          <Box />
        );
      case ACLObjtypeEnum.Entry:
        return entryRetrieve != null ? (
          <EntryBreadcrumbs entry={entryRetrieve} title="ACL変更履歴" />
        ) : (
          <Box />
        );
      default:
        return <Box />;
    }
  })();

  const controlMenu = () => {
    switch (acl.objtype) {
      case ACLObjtypeEnum.Entity:
        return (
          <EntityControlMenu
            entityId={acl.id}
            anchorElem={anchorEl}
            handleClose={() => setAnchorEl(null)}
            setOpenImportModal={setOpenImportModal}
            permission={entityDetail?.permission}
          />
        );
      case ACLObjtypeEnum.Entry:
        if (acl.parent?.id) {
          return (
            <EntryControlMenu
              entityId={acl.parent.id}
              entryId={acl.id}
              anchorElem={anchorEl}
              handleClose={() => setAnchorEl(null)}
              permission={entryRetrieve?.permission}
              entityPermission={entryRetrieve?.schema?.permission}
            />
          );
        }
    }
  };

  return (
    <>
      {breadcrumbs}

      <PageHeader title={acl.name} description="ACL変更履歴">
        <MenuBox>
          <IconButton
            id="controlMenu"
            onClick={(e) => {
              setAnchorEl(e.currentTarget);
            }}
          >
            <AppsIcon />
          </IconButton>
          {controlMenu()}
        </MenuBox>
      </PageHeader>
      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />

      <Container>
        <ACLHistoryList histories={aclHistory} />
      </Container>
    </>
  );
};

export const ACLHistoryPage: FC = () => {
  const { objectId } = useTypedParams<{ objectId: number }>();

  preload(
    ["acl", objectId],
    wrapFetcher(() => aironeApiClient.getAcl(objectId)),
  );
  preload(
    ["aclHistory", objectId],
    wrapFetcher(() => aironeApiClient.getAclHistory(objectId)),
  );

  return (
    <Box className="container-fluid">
      <Suspense fallback={<Loading />}>
        <ACLHistoryContent objectId={objectId} />
      </Suspense>
    </Box>
  );
};
