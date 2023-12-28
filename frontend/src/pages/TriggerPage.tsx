import {
  Box,
  Container,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { usePage } from "hooks/usePage";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";

const HeaderTableRow = styled(TableRow)(({ }) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({ }) => ({
  color: "#FFFFFF",
}));

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#607D8B0A",
  },
  "& td": {
    padding: "8px 16px",
  },
}));

const StyledBox = styled(Box)(() => ({
  display: "flex",
  gap: "20px",
}));

const TriggerCondition: FC<{
  cond: any;
}> = ({ cond }) => {
  return cond ? (
    <StyledBox key={cond.id}>
      <Box>{cond.attr.name}</Box>
      <Divider orientation="vertical" flexItem />
      <Box>
        {cond.strCond}
      </Box>
    </StyledBox>
  ) : (
    <Box />
  );
};

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
            <>
              <Table>
                <TableHead>
                  <HeaderTableRow>
                    <HeaderTableCell width="140px">
                      エンティティ
                    </HeaderTableCell>
                    <HeaderTableCell width="140px">条件</HeaderTableCell>
                    <HeaderTableCell width="140px">アクション</HeaderTableCell>
                  </HeaderTableRow>
                </TableHead>
                <TableBody>
                  {triggers.value?.results?.map((trigger) => {
                    return (
                      <StyledTableRow key={trigger.id}>
                        <TableCell>{trigger.entity.name}</TableCell>
                        <TableCell>
                          {trigger.conditions?.map((condition) => {
                            return (
                              <TriggerCondition cond={condition} />
                            );
                          })}
                        </TableCell>
                        <TableCell>
                          {trigger.actions.map((action) => {
                            return (
                              <Box key={action.id}>
                                <Typography>{action.attr.name}</Typography>
                                <Typography>
                                  {action.values.map((value) => {
                                    return (
                                      <Box key={value.id}>
                                        <Typography>{value.strCond}</Typography>
                                      </Box>
                                    );
                                  })}
                                </Typography>
                              </Box>
                            );
                          })}
                        </TableCell>
                      </StyledTableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </>
          )}
        </Box>
      </Container>
    </Box>
  );
};
