import SettingsIcon from "@mui/icons-material/Settings";
import { Box, Button, Typography } from "@mui/material";
import React, { FC, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { PageHeader } from "../components/common/PageHeader";

import { advancedSearchPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { AdvancedSearchModal } from "components/entry/AdvancedSearchModal";
import { SearchResults } from "components/entry/SearchResults";

export const AdvancedSearchResultsPage: FC = () => {
  const location = useLocation();
  const [openModal, setOpenModal] = useState(false);

  const params = new URLSearchParams(location.search);
  const entityIds = params.getAll("entity").map((id) => Number(id));
  const entryName = params.has("entry_name") ? params.get("entry_name") : "";
  const attrInfo = params.has("attrinfo")
    ? JSON.parse(params.get("attrinfo"))
    : [];

  const results = useAsync(async () => {
    const resp = await aironeApiClientV2.advancedSearchEntries(
      entityIds,
      entryName,
      attrInfo
    );
    const data = await resp.json();
    return data.result.ret_values;
  });

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
        subTitle={`${results.value?.length ?? 0} 件`}
        componentSubmits={
          <Box display="flex" justifyContent="center">
            <Button
              variant="outlined"
              startIcon={<SettingsIcon />}
              onClick={() => {
                setOpenModal(true);
              }}
            >
              高度な検索
            </Button>
            <Button sx={{ marginLeft: "40px" }} variant="outlined">
              YAML 出力
            </Button>
            <Button sx={{ marginLeft: "16px" }} variant="outlined">
              CSV 出力
            </Button>
          </Box>
        }
      />

      <Box sx={{ marginTop: "111px", paddingLeft: "10%", paddingRight: "10%" }}>
        {!results.loading ? (
          <SearchResults
            results={results.value}
            defaultEntryFilter={entryName}
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
        />
      </Box>
    </Box>
  );
};
