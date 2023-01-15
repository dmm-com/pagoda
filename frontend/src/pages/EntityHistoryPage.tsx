import AppsIcon from "@mui/icons-material/Apps";
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

import { entitiesPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";

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
        <Typography color="textPrimary">変更履歴</Typography>
      </AironeBreadcrumbs>

      <Container maxWidth="lg" sx={{ marginTop: "111px" }}>
        {/* NOTE: This Box component that has CSS tuning should be custom component */}
        <Box
          display="flex"
          sx={{ borderBottom: 1, borderColor: "gray", mb: "64px", pb: "64px" }}
        >
          <Box width="50px" />
          <Box flexGrow="1">
            {!entity.loading && (
              <Typography
                variant="h2"
                align="center"
                sx={{
                  margin: "auto",
                  maxWidth: "md",
                  textOverflow: "ellipsis",
                  overflow: "hidden",
                  whiteSpace: "nowrap",
                }}
              >
                {entity.value?.name}
              </Typography>
            )}
            <Typography variant="h4" align="center">
              変更履歴
            </Typography>
          </Box>
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
        </Box>

        {histories.loading ? (
          <Loading />
        ) : (
          <EntityHistoryList
            histories={histories.value?.results ?? []}
            page={page}
            maxPage={maxPage}
            handleChangePage={changePage}
          />
        )}
      </Container>

      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />
    </Box>
  );
};
