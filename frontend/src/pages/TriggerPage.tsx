import { Box, Container, Typography } from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { usePage } from "hooks/usePage";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";

export const TriggerPage: FC = () => {
  const [page, changePage] = usePage();
  const [keyword, setKeyword] = useState("");
  const params = new URLSearchParams(location.search);
  const [query, setQuery] = useState<string>(params.get("query") ?? "");
  const [toggle, setToggle] = useState(false);

  const triggers = useAsync(async () => {
    return await aironeApiClientV2.getTriggers(page);
  }, [page, query, toggle]);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">トリガー管理</Typography>
      </AironeBreadcrumbs>
      <PageHeader title="トリガー管理"></PageHeader>
      <Container>
        <Box>
          {triggers.loading ? (
            <Loading />
          ) : (
            <Box>
              {triggers.value?.results?.map((trigger) => {
                return (
                  <Box key={trigger.id}>
                    <Typography>{trigger.parent.entity.name}</Typography>
                  </Box>
                );
              })}
            </Box>
          )}
        </Box>
      </Container>
    </Box>
  );
};
