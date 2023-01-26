import AppsIcon from "@mui/icons-material/Apps";
import LockIcon from "@mui/icons-material/Lock";
import { Box, Container, IconButton, Typography } from "@mui/material";
import React, { FC, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { EntityControlMenu } from "../components/entity/EntityControlMenu";
import { EntityHistoryList } from "../components/entity/EntityHistoryList";
import { EntryImportModal } from "../components/entry/EntryImportModal";
import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { usePage } from "../hooks/usePage";
import { useTypedParams } from "../hooks/useTypedParams";
import { EntityHistoryList as ConstEntityHistoryList } from "../utils/Constants";

import { entitiesPath, entityEntriesPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";

export const EntityHistoryPage: FC = () => {
  const { entityId } = useTypedParams<{ entityId: number }>();

  const [page, changePage] = usePage();

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

  const entity = useAsyncWithThrow(async () => {
    return await aironeApiClientV2.getEntity(entityId);
  }, [entityId]);
  const histories = useAsync(async () => {
    return await aironeApiClientV2.getEntityHistories(entityId, page);
  }, [entityId, page]);

  const maxPage = useMemo(() => {
    if (histories.loading) {
      return 0;
    }
    return Math.ceil(
      histories.value?.count ?? 0 / ConstEntityHistoryList.MAX_ROW_COUNT
    );
  }, [histories.loading, histories.value?.count]);

  return (
    <Box className="container">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        {entity.value && (
          <Box sx={{ display: "flex" }}>
            <Typography
              component={Link}
              to={entityEntriesPath(entity.value.id)}
            >
              {entity.value.name}
            </Typography>
            {!entity.value.isPublic && <LockIcon />}
          </Box>
        )}
        <Typography color="textPrimary">変更履歴</Typography>
      </AironeBreadcrumbs>

      <PageHeader title={entity.value?.name} description="変更履歴">
        <Box width="50px">
          <IconButton
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
          />
        </Box>
      </PageHeader>

      {histories.loading ? (
        <Loading />
      ) : (
        <Container>
          <EntityHistoryList
            histories={histories.value?.results ?? []}
            page={page}
            maxPage={maxPage}
            handleChangePage={changePage}
          />
        </Container>
      )}

      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />
    </Box>
  );
};
