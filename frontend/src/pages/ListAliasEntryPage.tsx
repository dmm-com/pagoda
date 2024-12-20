import { EntryBase } from "@dmm-com/airone-apiclient-typescript-fetch";
import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, Grid, IconButton } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLocation } from "react-use";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";

import { PaginationFooter } from "components";
import { PageHeader } from "components/common/PageHeader";
import { SearchBox } from "components/common/SearchBox";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntityControlMenu } from "components/entity/EntityControlMenu";
import { AliasEntryList } from "components/entry/AliasEntryList";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { useFormNotification, usePage } from "hooks";
import { aironeApiClient } from "repository/AironeApiClient";
import {
  EntryListParam,
  extractAPIException,
  isResponseError,
  normalizeToMatch,
} from "services";

export const ListAliasEntryPage: FC = ({}) => {
  const { entityId } = useTypedParams<{
    entityId: number;
  }>();

  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const navigate = useNavigate();
  const { enqueueSubmitResult } = useFormNotification("エイリアス", true);
  const { enqueueSnackbar } = useSnackbar();
  const [page, changePage] = usePage();
  const [query, setQuery] = useState<string>(params.get("query") ?? "");

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

  const [entries, setEntries] = useState<EntryBase[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);

  const entity = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntity(entityId);
  }, [entityId]);

  useEffect(() => {
    aironeApiClient.getEntries(entityId, true, page, query).then((res) => {
      setEntries(res.results);
      setTotalCount(res.count);
    });
  }, [page, query]);

  const handleChangeQuery = (newQuery?: string) => {
    changePage(1);
    setQuery(newQuery ?? "");

    navigate({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  const handleCreate = (entryId: number, target: HTMLInputElement) => {
    const name = target.value;
    aironeApiClient
      .createEntryAlias(entryId, name)
      .then((resp) => {
        setEntries(
          entries.map((entry) => {
            if (entry.id === entryId) {
              return {
                ...entry,
                aliases: [...entry.aliases, resp],
              };
            } else {
              return entry;
            }
          })
        );
        target.value = "";
        enqueueSubmitResult(true);
      })
      .catch((e) => {
        if (e instanceof Error && isResponseError(e)) {
          extractAPIException(
            e,
            (message) => enqueueSubmitResult(false, `詳細: "${message}"`),
            (name, message) => enqueueSubmitResult(false, `詳細: "${message}"`)
          );
        } else {
          enqueueSubmitResult(false);
        }
      });
  };

  const handleDelete = (id: number) => {
    aironeApiClient
      .deleteEntryAlias(id)
      .then(() => {
        setEntries(
          entries.map((entry) => {
            return {
              ...entry,
              aliases: entry.aliases.filter((alias) => alias.id !== id),
            };
          })
        );
        enqueueSnackbar("エイリアスの削除が完了しました。", {
          variant: "success",
        });
      })
      .catch(() => {
        enqueueSnackbar("エイリアスの削除が失敗しました。", {
          variant: "error",
        });
      });
  };

  return (
    <Box>
      <EntityBreadcrumbs entity={entity.value} title="エイリアス設定" />

      <PageHeader title={entity.value?.name ?? ""} description="エイリアス設定">
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
          />
        </Box>
      </PageHeader>

      <Container>
        <Box width="600px" mb="16px">
          <SearchBox
            placeholder="アイテムを絞り込む"
            onKeyPress={(e) => {
              e.key === "Enter" &&
                handleChangeQuery(
                  normalizeToMatch((e.target as HTMLInputElement).value ?? "")
                );
            }}
          />
        </Box>
        {/* show all Aliases that are associated with each Items */}
        {entries.map((entry) => (
          <Grid
            key={entry.id}
            container
            my="4px"
            display="flex"
            alignItems="center"
          >
            <Grid item xs={4}>
              {entry.name}
            </Grid>
            <Grid item xs={8}>
              <AliasEntryList
                entry={entry}
                handleCreate={handleCreate}
                handleDelete={handleDelete}
              />
            </Grid>
          </Grid>
        ))}
        <PaginationFooter
          count={totalCount}
          maxRowCount={EntryListParam.MAX_ROW_COUNT}
          page={page}
          changePage={changePage}
        />
      </Container>

      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />
    </Box>
  );
};
