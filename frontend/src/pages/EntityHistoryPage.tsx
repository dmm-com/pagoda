import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import { FC, Suspense, useState } from "react";
import { preload } from "swr";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntityControlMenu } from "components/entity/EntityControlMenu";
import { EntityHistoryList } from "components/entity/EntityHistoryList";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { usePage } from "hooks/usePage";
import { usePagodaSWR, wrapFetcher } from "hooks/usePagodaSWR";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";

const EntityHistoryContent: FC<{
  entityId: number;
  page: number;
  changePage: (page: number) => void;
}> = ({ entityId, page, changePage }) => {
  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = useState(false);

  const { data: entity } = usePagodaSWR(
    ["entity", entityId],
    () => aironeApiClient.getEntity(entityId),
    { suspense: true },
  );
  const { data: histories } = usePagodaSWR(
    ["entityHistories", entityId, page],
    () => aironeApiClient.getEntityHistories(entityId, page),
    { suspense: true },
  );

  return (
    <>
      <EntityBreadcrumbs entity={entity} title="変更履歴" />

      <PageHeader title={entity.name} description="変更履歴">
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
        <EntityHistoryList
          histories={histories}
          page={page}
          changePage={changePage}
        />
      </Container>

      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />
    </>
  );
};

export const EntityHistoryPage: FC = () => {
  const { entityId } = useTypedParams<{ entityId: number }>();
  const { page, changePage } = usePage();

  preload(
    ["entity", entityId],
    wrapFetcher(() => aironeApiClient.getEntity(entityId)),
  );
  preload(
    ["entityHistories", entityId, page],
    wrapFetcher(() => aironeApiClient.getEntityHistories(entityId, page)),
  );

  return (
    <Box className="container">
      <Suspense fallback={<Loading />}>
        <EntityHistoryContent
          entityId={entityId}
          page={page}
          changePage={changePage}
        />
      </Suspense>
    </Box>
  );
};
