import {
  AdvancedSearchResult,
  AdvancedSearchResultAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import SettingsIcon from "@mui/icons-material/Settings";
import { IconButton, Box, Button, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import React, { FC, useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { advancedSearchPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Confirmable } from "components/common/Confirmable";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { RateLimitedClickable } from "components/common/RateLimitedClickable";
import { AdvancedSearchModal } from "components/entry/AdvancedSearchModal";
import { SearchResults } from "components/entry/SearchResults";
import { usePage } from "hooks/usePage";
import { aironeApiClient } from "repository/AironeApiClient";
import { AdvancedSerarchResultList } from "services/Constants";
import { extractAdvancedSearchParams } from "services/entry/AdvancedSearch";

export const getIsFiltered = (filterKey?: number, keyword?: string) => {
  switch (filterKey) {
    case AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY:
    case AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY:
    case AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED:
      return true;
    case AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED:
      return keyword !== "";
    case AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED:
      return keyword !== "";
  }

  return false;
};

const FullWidthIconBox = styled(IconButton)(({}) => ({
  width: "100%",
}));

export interface AirOneAdvancedSearchResult extends AdvancedSearchResult {
  offset: number;
  page: number;
  isInProcessing: boolean;
  isJoinSearching: boolean;
  totalCount: number;
}

export const AdvancedSearchResultsPage: FC = () => {
  const location = useLocation();
  const { enqueueSnackbar } = useSnackbar();
  const [page, changePage] = usePage();

  const [openModal, setOpenModal] = useState(false);
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

  const [searchResults, setSearchResults] =
    useState<AirOneAdvancedSearchResult>({
      count: 0,
      values: [],
      offset: 0,
      page: page,
      isInProcessing: true,
      isJoinSearching: joinAttrs.length > 0,
      totalCount: 0,
    });

  const entityAttrs = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntityAttrs(entityIds, searchAllEntities);
  });

  const handleSetResults = (isJoinSearching: boolean = false) => {
    setSearchResults({
      count: 0,
      values: [],
      offset: 0,
      page: page,
      isInProcessing: true,
      isJoinSearching: isJoinSearching,
      totalCount: searchResults.totalCount,
    });
  };

  useEffect(() => {
    const sendSearchRequest = function (offset: number) {
      return aironeApiClient.advancedSearch(
        entityIds,
        entryName,
        attrInfo,
        joinAttrs,
        hasReferral,
        referralName,
        searchAllEntities,
        page,
        AdvancedSerarchResultList.MAX_ROW_COUNT,
        offset
      );
    };

    // pagination processing is prioritize than others
    if (page !== searchResults.page) {
      sendSearchRequest(0).then((results) => {
        setSearchResults({
          count: results.count,
          values: results.values,
          offset: page * AdvancedSerarchResultList.MAX_ROW_COUNT,
          page: page,
          isInProcessing: false,
          isJoinSearching: joinAttrs.some((x) => {
            return x.attrinfo.some((y) => {
              return getIsFiltered(y.filterKey, y.keyword);
            });
          }),
          totalCount: results.totalCount,
        });
      });
    }

    // abort when isInProcessing is false
    if (!searchResults.isInProcessing) {
      return;
    }

    sendSearchRequest(searchResults.offset).then((results) => {
      setSearchResults({
        ...searchResults,
        count: searchResults.count + results.count,
        values: searchResults.values.concat(results.values),
        offset: searchResults.offset + AdvancedSerarchResultList.MAX_ROW_COUNT,
        isInProcessing: false,
        isJoinSearching: searchResults.isJoinSearching,
        totalCount: results.totalCount,
      });
    });
  }, [page, toggle, location.search, searchResults]);

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
      enqueueSnackbar("複数アイテムの削除に成功しました", {
        variant: "success",
      });
      setBulkOperationEntryIds([]);
      setToggle(!toggle);
    } catch (e) {
      enqueueSnackbar("複数アイテムの削除に失敗しました", {
        variant: "error",
      });
    }
  };

  const getSearchProgress = () => {
    if (searchResults.isInProcessing) {
      return "検索中...";
    } else if (searchResults.count < searchResults.totalCount) {
      return `${searchResults.count ?? 0} / ${searchResults.totalCount} 件`;
    } else {
      return `${searchResults.count ?? 0} 件`;
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

      <PageHeader title="検索結果" description={getSearchProgress()}>
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

      {searchResults.count === 0 && searchResults.isInProcessing ? (
        <Loading />
      ) : (
        <Box>
          <SearchResults
            results={searchResults}
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
            entityIds={entityIds}
            searchAllEntities={searchAllEntities}
            joinAttrs={joinAttrs}
            disablePaginationFooter={joinAttrs.length > 0}
            setSearchResults={handleSetResults}
          />

          {/* show button to show continuous search results manually when joinAttrs are specified */}
          {joinAttrs.length > 0 && (
            <FullWidthIconBox
              disabled={
                searchResults.isInProcessing ||
                searchResults.count >= searchResults.totalCount
              }
              onClick={() =>
                setSearchResults({ ...searchResults, isInProcessing: true })
              }
            >
              <ArrowDropDownIcon />
            </FullWidthIconBox>
          )}
        </Box>
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
    </Box>
  );
};
