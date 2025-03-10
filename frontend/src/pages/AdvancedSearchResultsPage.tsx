import {
  AdvancedSearchResult,
  AdvancedSearchResultAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import SettingsIcon from "@mui/icons-material/Settings";
import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Confirmable } from "components/common/Confirmable";
import { CenterAlignedBox } from "components/common/FlexBox";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { RateLimitedClickable } from "components/common/RateLimitedClickable";
import { AdvancedSearchModal } from "components/entry/AdvancedSearchModal";
import { SearchResults } from "components/entry/SearchResults";
import { usePage } from "hooks/usePage";
import { aironeApiClient } from "repository/AironeApiClient";
import { advancedSearchPath, topPath } from "routes/Routes";
import { AdvancedSerarchResultListParam } from "services/Constants";
import { extractAdvancedSearchParams } from "services/entry/AdvancedSearch";

function isAttrInfoSet(info: AdvancedSearchResultAttrInfo) {
  switch (info.filterKey) {
    case AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED:
      return false;
    case AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY:
    case AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY:
    case AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED:
    case AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED:
      return true;
    case AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED:
      return info.keyword !== "";
    default:
      return false;
  }
}

function DeleteAllLabel(attrinfo: Array<AdvancedSearchResultAttrInfo>) {
  const renderLabel = (info: AdvancedSearchResultAttrInfo) => {
    switch (info.filterKey) {
      case AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY:
        return "(空白)";
      case AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY:
        return "(空白ではない)";
      case AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED:
        return "(重複している)";
      case AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED:
        return `「${info.keyword}」を含む`;
      case AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED:
        return `「${info.keyword}」を含まない`;
      default:
        return "";
    }
  };

  if (attrinfo.some((x) => isAttrInfoSet(x))) {
    return (
      <>
        <Typography>
          以下の条件にマッチする未選択の全てのアイテムを削除する
        </Typography>
        <Typography variant="caption" color="warning">
          （↑のチェックを入れない場合、一覧で選択したアイテムのみ削除されます）
        </Typography>
        <Table size="small">
          <TableBody>
            {attrinfo.map((info, index) => {
              if (isAttrInfoSet(info)) {
                return (
                  <TableRow key={index}>
                    <TableCell>
                      <Typography>属性「{info.name}」の値が</Typography>
                    </TableCell>
                    <TableCell>{renderLabel(info)}</TableCell>
                  </TableRow>
                );
              }
            })}
          </TableBody>
        </Table>
      </>
    );
  } else {
    return <>未選択の全てのアイテムもまとめて削除する</>;
  }
}

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

export interface AirOneAdvancedSearchResult extends AdvancedSearchResult {
  page: number;
  isInProcessing: boolean;
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
  const [isDeleteAllItems, setIsDeleteAllItems] = useState(false);

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
      page: page,
      isInProcessing: true,
      totalCount: 0,
    });

  const entityAttrs = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntityAttrs(entityIds, searchAllEntities);
  });

  const handleSetResults = () => {
    setSearchResults({
      count: 0,
      values: [],
      page: page,
      isInProcessing: true,
      totalCount: 0,
    });
    setToggle(!toggle);
  };

  useEffect(() => {
    const sendSearchRequest = () => {
      return aironeApiClient.advancedSearch(
        entityIds,
        entryName,
        attrInfo,
        joinAttrs,
        hasReferral,
        referralName,
        searchAllEntities,
        page,
        AdvancedSerarchResultListParam.MAX_ROW_COUNT,
      );
    };

    // show loading indicator
    setSearchResults({ ...searchResults, isInProcessing: true });

    sendSearchRequest().then((results) => {
      if (joinAttrs.length > 0) {
        if (results.count === 0) {
          changePage(page + 1);
          return;
        }
        setSearchResults({
          ...searchResults,
          count: searchResults.count + results.count,
          values: searchResults.values.concat(results.values),
          page: page,
          totalCount: results.totalCount,
          isInProcessing: false,
        });
      } else {
        setSearchResults({
          count: results.count,
          values: results.values,
          page: page,
          totalCount: results.totalCount,
          isInProcessing: false,
        });
      }
    });
  }, [page, toggle, location.search]);

  const handleExport = async (exportStyle: "yaml" | "csv") => {
    try {
      await aironeApiClient.exportAdvancedSearchResults(
        entityIds,
        attrInfo,
        entryName,
        hasReferral,
        searchAllEntities,
        exportStyle,
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

  const handleBulkDelete = async () => {
    try {
      await aironeApiClient.destroyEntries(
        bulkOperationEntryIds,
        JSON.stringify(
          attrInfo.map((info) => ({
            name: info.name,
            filterKey: String(info.filterKey),
            keyword: info.keyword,
          })),
        ),
        // disable isDeleteAllItems when join-attrs are specified
        isDeleteAllItems && joinAttrs.length == 0,
      );
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
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography component={AironeLink} to={advancedSearchPath()}>
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
            content={
              bulkOperationEntryIds.length ==
                AdvancedSerarchResultListParam.MAX_ROW_COUNT &&
              joinAttrs.length == 0 ? (
                <FormControlLabel
                  sx={
                    attrInfo.some((x) => isAttrInfoSet(x))
                      ? { alignItems: "flex-start" }
                      : {}
                  }
                  control={
                    <Checkbox onChange={() => setIsDeleteAllItems(true)} />
                  }
                  label={DeleteAllLabel(attrInfo)}
                />
              ) : (
                <></>
              )
            }
          />
        </Box>
      </PageHeader>

      {joinAttrs.length === 0 && searchResults.isInProcessing ? (
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
                  const base = {
                    key: info.name,
                    val: {
                      filterKey:
                        info.filterKey ||
                        AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
                      keyword: info.keyword || "",
                    },
                  };

                  const joined = joinAttrs
                    .filter((join) => join.name === info.name)
                    .flatMap((join) =>
                      join.attrinfo.map((joinedInfo) => ({
                        key: `${join.name}.${joinedInfo.name}`,
                        val: {
                          filterKey:
                            joinedInfo.filterKey ||
                            AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
                          keyword: joinedInfo.keyword || "",
                          baseAttrname: join.name,
                          joinedAttrname: joinedInfo.name,
                        },
                      })),
                    );

                  return [base, ...joined];
                })
                .flat()
                .reduce((a, x) => ({ ...a, [x.key]: x.val }), {})
            }
            bulkOperationEntryIds={bulkOperationEntryIds}
            setBulkOperationEntryIds={setBulkOperationEntryIds}
            entityIds={entityIds}
            searchAllEntities={searchAllEntities}
            joinAttrs={joinAttrs}
            disablePaginationFooter={joinAttrs.length > 0}
            setSearchResults={handleSetResults}
          />

          {/* show button to show continuous search results manually when joinAttrs are specified */}
          {joinAttrs.length > 0 && (
            <>
              {searchResults.isInProcessing ? (
                <Loading />
              ) : (
                <CenterAlignedBox alignItems="center">
                  <IconButton
                    disabled={searchResults.count >= searchResults.totalCount}
                    onClick={() => changePage(searchResults.page + 1)}
                  >
                    <ArrowDropDownIcon />
                  </IconButton>
                  <Typography>
                    {page * AdvancedSerarchResultListParam.MAX_ROW_COUNT} /{" "}
                    {searchResults.totalCount} 件
                  </Typography>
                </CenterAlignedBox>
              )}
            </>
          )}
        </Box>
      )}

      <AdvancedSearchModal
        openModal={openModal}
        setOpenModal={setOpenModal}
        attrNames={entityAttrs.value ?? []}
        initialAttrNames={attrInfo.map(
          (e: AdvancedSearchResultAttrInfo) => e.name,
        )}
        attrInfos={attrInfo}
      />
    </Box>
  );
};
