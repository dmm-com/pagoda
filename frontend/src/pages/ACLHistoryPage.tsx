import {
  ACLObjtypeEnum,
  EntityDetail,
  EntryRetrieve,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, Suspense, useEffect, useState } from "react";
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
  const [breadcrumbs, setBreadcrumbs] = useState<JSX.Element>(<Box />);
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = useState(false);
  const [entityDetail, setEntityDetail] = useState<EntityDetail | null>(null);
  const [entryRetrieve, setEntryRetrieve] = useState<EntryRetrieve | null>(
    null,
  );

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

  useEffect(() => {
    switch (acl.objtype) {
      case ACLObjtypeEnum.Entity:
        aironeApiClient.getEntity(objectId).then((resp) => {
          setEntityDetail(resp);
          setBreadcrumbs(
            <EntityBreadcrumbs entity={resp} title="ACL変更履歴" />,
          );
        });
        break;
      case ACLObjtypeEnum.Entry:
        aironeApiClient.getEntry(objectId).then((resp) => {
          setEntryRetrieve(resp);
          setBreadcrumbs(<EntryBreadcrumbs entry={resp} title="ACL変更履歴" />);
        });
        break;
    }
  }, [acl]);

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
