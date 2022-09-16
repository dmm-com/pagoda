import SettingsIcon from "@mui/icons-material/Settings";
import { Box, Button, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { PageHeader } from "../components/common/PageHeader";
import { RateLimitedClickable } from "../components/common/RateLimitedClickable";

import { advancedSearchPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { AdvancedSearchModal } from "components/entry/AdvancedSearchModal";
import { SearchResults } from "components/entry/SearchResults";
import {
  exportAdvancedSearchResults,
  getEntityAttrs,
} from "utils/AironeAPIClient";

export const AdvancedSearchResultsPage: FC = () => {
  const location = useLocation();
  const { enqueueSnackbar } = useSnackbar();
  const [openModal, setOpenModal] = useState(false);

  const params = new URLSearchParams(location.search);
  const entityIds = params.getAll("entity").map((id) => Number(id));
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

  const entityAttrs = useAsync(async () => {
    const resp = await getEntityAttrs(entityIds);
    const data = await resp.json();

    return data.result;
  });

  const results = useAsync(async () => {
    const resp = await aironeApiClientV2.advancedSearchEntries(
      entityIds,
      entryName,
      attrInfo,
      hasReferral,
      referralName
    );
    const data = await resp.json();
    return data.result;
  });

  const handleExport = async (exportStyle: "yaml" | "csv") => {
    const resp = await exportAdvancedSearchResults(
      entityIds,
      attrInfo,
      entryName,
      hasReferral,
      exportStyle
    );
    if (resp.ok) {
      enqueueSnackbar("エクスポートジョブの登録に成功しました", {
        variant: "success",
      });
    } else {
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
        subTitle={`${results.value?.ret_count ?? 0} 件`}
        componentSubmits={
          <Box display="flex" justifyContent="center">
            <Button
              variant="outlined"
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
              <Button sx={{ marginLeft: "40px" }} variant="outlined">
                YAML 出力
              </Button>
            </RateLimitedClickable>
            <RateLimitedClickable
              intervalSec={5}
              onClick={() => handleExport("csv")}
            >
              <Button sx={{ marginLeft: "16px" }} variant="outlined">
                CSV 出力
              </Button>
            </RateLimitedClickable>
          </Box>
        }
      />

      <Box sx={{ marginTop: "111px", paddingLeft: "10%", paddingRight: "10%" }}>
        {!results.loading ? (
          <SearchResults
            results={results.value.ret_values}
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
    </Box>
  );
};
