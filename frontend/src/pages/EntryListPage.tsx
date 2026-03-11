import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import { FC, Suspense, useState } from "react";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntityControlMenu } from "components/entity/EntityControlMenu";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { EntryList } from "components/entry/EntryList";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { TITLE_TEMPLATES } from "services";
import { canEdit } from "services/ACLUtil";

interface Props {
  canCreateEntry?: boolean;
}

const EntryListContent: FC<Props> = ({ canCreateEntry = true }) => {
  const { entityId } = useTypedParams<{ entityId: number }>();

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = useState(false);

  const { data: entity } = usePagodaSWR(
    ["entity", entityId],
    () => aironeApiClient.getEntity(entityId),
    { suspense: true },
  );

  usePageTitle(TITLE_TEMPLATES.entryList, {
    prefix: entity.name,
  });

  return (
    <>
      <EntityBreadcrumbs entity={entity} />

      <PageHeader
        title={entity.name}
        description="アイテム一覧"
        targetId={entity.id}
        hasOngoingProcess={entity.hasOngoingChanges}
      >
        <Box width="50px">
          <IconButton
            id="entity_menu"
            onClick={(e) => {
              setEntityAnchorEl(e.currentTarget);
            }}
          >
            <AppsIcon />
          </IconButton>
          <EntityControlMenu
            entityId={entityId}
            anchorElem={entityAnchorEl}
            handleClose={() => setEntityAnchorEl(null)}
            setOpenImportModal={setOpenImportModal}
            permission={entity.permission}
          />
        </Box>
      </PageHeader>

      <Container>
        <EntryList
          entityId={entityId}
          canCreateEntry={
            canCreateEntry &&
            (entity.permission === undefined || canEdit(entity.permission))
          }
        />
      </Container>
      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />
    </>
  );
};

export const EntryListPage: FC<Props> = ({ canCreateEntry = true }) => {
  return (
    <Box>
      <Suspense fallback={<Loading />}>
        <EntryListContent canCreateEntry={canCreateEntry} />
      </Suspense>
    </Box>
  );
};
