import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import { FC, Suspense, useState } from "react";

import { usePagodaSWR } from "../hooks/usePagodaSWR";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntityControlMenu } from "components/entity/EntityControlMenu";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { RestorableEntryList } from "components/entry/RestorableEntryList";
import { useIdParams } from "hooks/useIdParams";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";

const EntryRestoreContent: FC<{ entityId: number }> = ({ entityId }) => {
  const { t } = useTranslation();
  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = useState(false);

  const { data: entity } = usePagodaSWR(
    ["entity", entityId],
    () => aironeApiClient.getEntity(entityId),
    { suspense: true },
  );

  return (
    <>
      <EntityBreadcrumbs entity={entity} title={t("common.restore")} />

      <PageHeader
        title={entity.name}
        description={t("entry.restorePage.description")}
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
          <EntryImportModal
            openImportModal={openImportModal}
            closeImportModal={() => setOpenImportModal(false)}
          />
        </Box>
      </PageHeader>

      <Container>
        <RestorableEntryList entityId={entityId} />
      </Container>
    </>
  );
};

export const EntryRestorePage: FC = () => {
  const { entityId } = useIdParams({ required: ["entityId"] });

  return (
    <Box>
      <Suspense fallback={<Loading />}>
        <EntryRestoreContent entityId={entityId} />
      </Suspense>
    </Box>
  );
};
