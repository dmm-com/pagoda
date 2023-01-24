import SettingsIcon from "@mui/icons-material/Settings";
import { Box, Button, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { PageHeader } from "../components/common/PageHeader";
import { RateLimitedClickable } from "../components/common/RateLimitedClickable";
import { usePage } from "../hooks/usePage";
import { AdvancedSerarchResultList } from "../utils/Constants";

import { advancedSearchPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { AdvancedSearchModal } from "components/entry/AdvancedSearchModal";
import { SearchResults } from "components/entry/SearchResults";

export const AdvancedSearchResultsPage: FC = () => {
  const location = useLocation();
  const { enqueueSnackbar } = useSnackbar();

  const [page, changePage] = usePage();

  const params = new URLSearchParams(location.search);
  const entityIds = params.getAll("entity").map((id) => Number(id));
  const searchAllEntities = params.has("is_all_entities")
    ? params.get("is_all_entities") === "true"
    : false;
  const entryName = params.has("entry_name") ? params.get("entry_name") : "";
  const hasReferral = params.has("has_referral")
    ? params.get("has_referral") === "true"
    : false;
  const referralName = params.has("referral_name")
    ? params.get("referral_name")
    : "";
  const attrInfo = params.has("attrinfo")
    ? JSON.parse(params.get("attrinfo"))
    : [];

  const [openModal, setOpenModal] = useState(false);

  const entityAttrs = useAsync(async () => {
    return await aironeApiClientV2.getEntityAttrs(entityIds, searchAllEntities);
  });

  const results = useAsync(async () => {
    const resp = await aironeApiClientV2.advancedSearchEntries(
      entityIds,
      entryName,
      attrInfo,
      hasReferral,
      referralName,
      searchAllEntities,
      page
    );
    const data = await resp.json();
    return data.result;
  }, [page]);

  const maxPage = useMemo(() => {
    if (results.loading) {
      return 0;
    }
    return Math.ceil(
      results.value.ret_count / AdvancedSerarchResultList.MAX_ROW_COUNT
    );
  }, [results.loading, results.value?.ret_count]);

  const handleExport = async (exportStyle: "yaml" | "csv") => {
    try {
      await aironeApiClientV2.exportAdvancedSearchResults(
        entityIds,
        attrInfo,
        entryName,
        hasReferral,
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

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        {attrInfo.length > 0 && (
          <Typography component={Link} to={advancedSearchPath()}>
            高度な検索
          </Typography>
        )}
        <Typography color="textPrimary">検索結果</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title="検索結果"
        description={`${results.value?.ret_count ?? 0} 件`}
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
        </Box>
      </PageHeader>

      {!results.loading ? (
        <SearchResults
          results={results.value.ret_values}
          page={page}
          maxPage={maxPage}
          handleChangePage={changePage}
          defaultEntryFilter={entryName}
          defaultReferralFilter={referralName}
          defaultAttrsFilter={Object.fromEntries(
            attrInfo.map((i) => [i["name"], i["keyword"] || ""])
          )}
        />
      ) : (
        <Loading />
      )}
      <AdvancedSearchModal
        openModal={openModal}
        setOpenModal={setOpenModal}
        attrNames={entityAttrs.loading ? [] : entityAttrs.value}
        initialAttrNames={attrInfo.map((e) => e.name)}
      />
    </Box>
  );
};
