import AddIcon from "@mui/icons-material/Add";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardHeader,
  Grid,
  IconButton,
  Pagination,
  Stack,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";

import { useAsyncWithThrow } from "../../hooks/useAsyncWithThrow";
import { usePage } from "../../hooks/usePage";
import { normalizeToMatch } from "../../services/StringUtil";

import { newEntryPath, entryDetailsPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { Loading } from "components/common/Loading";
import { SearchBox } from "components/common/SearchBox";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryList as ConstEntryList } from "services/Constants";

const StyledCard = styled(Card)(({}) => ({
  height: "100%",
}));

const StyledCardHeader = styled(CardHeader)(({}) => ({
  p: "0px",
  mt: "24px",
  mx: "16px",
  mb: "16px",
  ".MuiCardHeader-content": {
    width: "80%",
  },
}));

const EntryName = styled(Typography)(({}) => ({
  textOverflow: "ellipsis",
  overflow: "hidden",
  whiteSpace: "nowrap",
}));

interface Props {
  entityId: number;
  canCreateEntry?: boolean;
}

export const EntryList: FC<Props> = ({ entityId, canCreateEntry = true }) => {
  const location = useLocation();
  const history = useHistory();

  const [page, changePage] = usePage();

  const params = new URLSearchParams(location.search);

  const [query, setQuery] = useState<string>(params.get("query") ?? "");
  const [keyword, setKeyword] = useState(query ?? "");

  const entries = useAsyncWithThrow(async () => {
    return await aironeApiClientV2.getEntries(entityId, true, page, query);
  }, [page, query]);

  const handleChangeQuery = (newQuery?: string) => {
    changePage(1);
    setQuery(newQuery ?? "");

    history.push({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  const totalPageCount = entries.loading
    ? 0
    : Math.ceil((entries.value?.count ?? 0) / ConstEntryList.MAX_ROW_COUNT);

  const [entryAnchorEls, setEntryAnchorEls] = useState<{
    [key: number]: HTMLButtonElement | null;
  }>({});

  return (
    <Box>
      {/* This box shows search box and create button */}
      <Box display="flex" justifyContent="space-between" mb="16px">
        <Box width={500}>
          <SearchBox
            placeholder="エントリを絞り込む"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyPress={(e) => {
              e.key === "Enter" &&
                handleChangeQuery(
                  keyword.length > 0 ? normalizeToMatch(keyword) : undefined
                );
            }}
          />
        </Box>
        <Button
          color="secondary"
          variant="contained"
          disabled={!canCreateEntry}
          component={Link}
          to={newEntryPath(entityId)}
          sx={{ borderRadius: "24px" }}
        >
          <AddIcon />
          新規エントリを作成
        </Button>
      </Box>

      {/* This box shows each entry Cards */}
      {entries.loading ? (
        <Loading />
      ) : (
        <Grid container spacing={2}>
          {entries.value?.results?.map((entry) => {
            return (
              <Grid item xs={4} key={entry.id}>
                <StyledCard>
                  <StyledCardHeader
                    title={
                      <CardActionArea
                        component={Link}
                        to={entryDetailsPath(entityId, entry.id)}
                      >
                        <EntryName variant="h6">{entry.name}</EntryName>
                      </CardActionArea>
                    }
                    action={
                      <>
                        <IconButton
                          onClick={(e) => {
                            setEntryAnchorEls({
                              ...entryAnchorEls,
                              [entry.id]: e.currentTarget,
                            });
                          }}
                        >
                          <MoreVertIcon />
                        </IconButton>
                        <EntryControlMenu
                          entityId={entityId}
                          entryId={entry.id}
                          anchorElem={entryAnchorEls[entry.id]}
                          handleClose={(entryId: number) =>
                            setEntryAnchorEls({
                              ...entryAnchorEls,
                              [entryId]: null,
                            })
                          }
                        />
                      </>
                    }
                  />
                </StyledCard>
              </Grid>
            );
          })}
        </Grid>
      )}
      <Box display="flex" justifyContent="center" my="30px">
        <Stack spacing={2}>
          <Pagination
            count={totalPageCount}
            page={page}
            onChange={(_, newPage) => changePage(newPage)}
            color="primary"
          />
        </Stack>
      </Box>
    </Box>
  );
};
