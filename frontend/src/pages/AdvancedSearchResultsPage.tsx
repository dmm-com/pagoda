import {
  AdvancedSearchResultAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import SettingsIcon from "@mui/icons-material/Settings";
import { Box, Button, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { advancedSearchPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Confirmable } from "components/common/Confirmable";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { RateLimitedClickable } from "components/common/RateLimitedClickable";
import { AdvancedSearchJoinModal } from "components/entry/AdvancedSearchJoinModal";
import { AdvancedSearchModal } from "components/entry/AdvancedSearchModal";
import { SearchResults } from "components/entry/SearchResults";
import { usePage } from "hooks/usePage";
import { aironeApiClient } from "repository/AironeApiClient";
import { extractAdvancedSearchParams } from "services/entry/AdvancedSearch";

export const AdvancedSearchResultsPage: FC = () => {
  const location = useLocation();
  const { enqueueSnackbar } = useSnackbar();
  const [page, changePage] = usePage();

  const [openModal, setOpenModal] = useState(false);
  const [joinAttrname, setJoinAttrname] = useState("");
  const [bulkOperationEntryIds, setBulkOperationEntryIds] = useState<
    Array<number>
  >([]);
  const [toggle, setToggle] = useState(false);

  const {
    entityIds,
    searchAllEntities,
    entryName,
    hasReferral,
    referralName,
    attrInfo,
    joinAttrs,
  } = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return extractAdvancedSearchParams(params);
  }, [location.search]);

  const entityAttrs = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntityAttrs(entityIds, searchAllEntities);
  });

  const results = useAsyncWithThrow(async () => {
    return await aironeApiClient.advancedSearch(
      entityIds,
      entryName,
      attrInfo,
      joinAttrs,
      hasReferral,
      referralName,
      searchAllEntities,
      page
    );
  }, [page, toggle]);

  const handleExport = async (exportStyle: "yaml" | "csv") => {
    try {
      await aironeApiClient.exportAdvancedSearchResults(
        entityIds,
        attrInfo,
        entryName,
        hasReferral,
        searchAllEntities,
        exportStyle
      );
      enqueueSnackbar("エクスポートジョブの登録に成功しました", {
        variant: "success",
      });
    } catch (e) {
      enqueueSnackbar("エクスポートジョブの登録に失敗しました", {
        variant: "error",
      });
    }
  };

  const handleChangeBulkOperationEntryId = (id: number, checked: boolean) => {
    if (checked) {
      setBulkOperationEntryIds([...bulkOperationEntryIds, id]);
    } else {
      setBulkOperationEntryIds(bulkOperationEntryIds.filter((i) => i !== id));
    }
  };

  const handleBulkDelete = async () => {
    try {
      await aironeApiClient.destroyEntries(bulkOperationEntryIds);
      enqueueSnackbar("複数エントリの削除に成功しました", {
        variant: "success",
      });
      setBulkOperationEntryIds([]);
      setToggle(!toggle);
    } catch (e) {
      enqueueSnackbar("複数エントリの削除に失敗しました", {
        variant: "error",
      });
    }
  };

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={advancedSearchPath()}>
          高度な検索
        </Typography>
        <Typography color="textPrimary">検索結果</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title="検索結果"
        description={`${results.value?.count ?? 0} 件`}
      >
        <Box display="flex" justifyContent="center">
          <Button
            variant="contained"
            color="info"
            startIcon={<SettingsIcon />}
            disabled={entityAttrs.loading}
            onClick={() => {
              setOpenModal(true);
            }}
          >
            属性の再設定
          </Button>
          <RateLimitedClickable
            intervalSec={5}
            onClick={() => handleExport("yaml")}
          >
            <Button
              sx={{ marginLeft: "40px" }}
              variant="contained"
              color="info"
              disabled={joinAttrs.length > 0}
            >
              YAML 出力
            </Button>
          </RateLimitedClickable>
          <RateLimitedClickable
            intervalSec={5}
            onClick={() => handleExport("csv")}
          >
            <Button
              sx={{ marginLeft: "16px" }}
              variant="contained"
              color="info"
            >
              CSV 出力
            </Button>
          </RateLimitedClickable>
          <Confirmable
            componentGenerator={(handleOpen) => (
              <Button
                sx={{ marginLeft: "40px" }}
                variant="contained"
                color="info"
                startIcon={<DeleteOutlineIcon />}
                disabled={bulkOperationEntryIds.length === 0}
                onClick={handleOpen}
              >
                まとめて削除
              </Button>
            )}
            dialogTitle="本当に削除しますか？"
            onClickYes={handleBulkDelete}
          />
        </Box>
      </PageHeader>

      {results.loading || !results.value ? (
        <Loading />
      ) : (
        <SearchResults
          results={results.value}
          page={page}
          changePage={changePage}
          hasReferral={hasReferral}
          defaultEntryFilter={entryName}
          defaultReferralFilter={referralName}
          defaultAttrsFilter={
            // make defaultAttrFilter to make fabric contexts of joinAttrs into the one of attrinfo
            // for considering order of showing attribute by userdefined one and connection of
            // attrinfo and its related joined attrinfo
            attrInfo
              .map((info) => {
                const results = [];

                results.push({
                  key: info.name,
                  val: {
                    filterKey:
                      info.filterKey ||
                      AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
                    keyword: info.keyword || "",
                  },
                });

                // weave joined attributes into the defaultAttrFilterArray
                joinAttrs.forEach((join) => {
                  if (join.name === info.name) {
                    join.attrinfo.forEach((joinedInfo) => {
                      results.push({
                        key: `${join.name}.${joinedInfo.name}`,
                        val: {
                          filterKey:
                            joinedInfo.filterKey ||
                            AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
                          keyword: joinedInfo.keyword || "",
                          baseAttrname: join.name,
                          joinedAttrname: joinedInfo.name,
                        },
                      });
                    });
                  }
                });
                return results;

                // this convert array to dict using reduce()
              })
              .flat()
              .reduce((a, x) => ({ ...a, [x.key]: x.val }), {})
          }
          bulkOperationEntryIds={bulkOperationEntryIds}
          handleChangeBulkOperationEntryId={handleChangeBulkOperationEntryId}
          setJoinAttrname={setJoinAttrname}
        />
      )}
      <AdvancedSearchModal
        openModal={openModal}
        setOpenModal={setOpenModal}
        attrNames={entityAttrs.value ?? []}
        initialAttrNames={attrInfo.map(
          (e: AdvancedSearchResultAttrInfo) => e.name
        )}
        attrInfos={attrInfo}
      />
      <AdvancedSearchJoinModal
        targetEntityIds={entityIds}
        searchAllEntities={searchAllEntities}
        targetAttrname={joinAttrname}
        setJoinAttrname={setJoinAttrname}
        joinAttrs={joinAttrs}
      />
    </Box>
  );
};
