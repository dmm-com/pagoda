import {
  ACLObjtypeEnum,
  EntityDetail,
  EntryRetrieve,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, useEffect, useState } from "react";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

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

export const ACLHistoryPage: FC = () => {
  const { objectId } = useTypedParams<{ objectId: number }>();
  const [breadcrumbs, setBreadcrumbs] = useState<JSX.Element>(<Box />);
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = useState(false);
  const [entityDetail, setEntityDetail] = useState<EntityDetail | null>(null);
  const [entryRetrieve, setEntryRetrieve] = useState<EntryRetrieve | null>(
    null,
  );

  const acl = useAsyncWithThrow(async () => {
    return await aironeApiClient.getAcl(objectId);
  }, [objectId]);

  const aclHistory = useAsyncWithThrow(async () => {
    return await aironeApiClient.getAclHistory(objectId);
  }, [objectId]);

  const controlMenu = () => {
    if (acl.value == null) return;
    switch (acl.value.objtype) {
      case ACLObjtypeEnum.Entity:
        return (
          <EntityControlMenu
            entityId={acl.value.id}
            anchorElem={anchorEl}
            handleClose={() => setAnchorEl(null)}
            setOpenImportModal={setOpenImportModal}
            permission={entityDetail?.permission}
          />
        );
      case ACLObjtypeEnum.Entry:
        if (acl.value.parent?.id) {
          return (
            <EntryControlMenu
              entityId={acl.value.parent.id}
              entryId={acl.value.id}
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
    if (acl.value == null) return;

    switch (acl.value.objtype) {
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
  }, [acl.loading]);

  return (
    <Box className="container-fluid">
      {breadcrumbs}

      <PageHeader title={acl.value?.name ?? ""} description="ACL変更履歴">
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

      {aclHistory.loading ? (
        <Loading />
      ) : (
        <Container>
          <ACLHistoryList histories={aclHistory.value ?? []} />
        </Container>
      )}
    </Box>
  );
};
