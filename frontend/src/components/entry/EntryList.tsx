import AddIcon from "@mui/icons-material/Add";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Box,
  Card,
  CardActionArea,
  CardHeader,
  Fab,
  Grid,
  IconButton,
  Pagination,
  Stack,
  Typography,
} from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";

import { newEntryPath, entryDetailsPath } from "Routes";
import { SearchBox } from "components/common/SearchBox";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryList as ConstEntryList } from "utils/Constants";

interface Props {
  entityId: string;
  entries: {
    id: number;
    name: string;
  }[];
  canCreateEntry?: boolean;
}

export const EntryList: FC<Props> = ({
  entityId,
  entries,
  canCreateEntry = true,
}) => {
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = React.useState(1);

  const handleChange = (event, value) => {
    setPage(value);
  };

  // FIXME paginate and get partial entries on BE V2 API side
  const filteredEntries = entries.filter((e) => {
    return e.name.indexOf(keyword) !== -1;
  });
  const displayedEntries = filteredEntries.slice(
    (page - 1) * ConstEntryList.MAX_ROW_COUNT,
    page * ConstEntryList.MAX_ROW_COUNT
  );

  const totalPageCount = Math.ceil(
    filteredEntries.length / ConstEntryList.MAX_ROW_COUNT
  );

  const [entryAnchorEls, setEntryAnchorEls] = useState<{
    [key: number]: HTMLButtonElement;
  } | null>({});

  return (
    <Box>
      {/* This box shows search box and create button */}
      <Box display="flex" justifyContent="space-between" mb={8}>
        <Box width={500}>
          <SearchBox
            placeholder="エントリを絞り込む"
            value={keyword}
            onChange={(e) => {
              setKeyword(e.target.value);

              /* Reset page number to prevent vanishing entities from display
               * when user move other page */
              setPage(1);
            }}
          />
        </Box>
        <Fab
          disabled={!canCreateEntry}
          color="secondary"
          aria-label="add"
          variant="extended"
          component={Link}
          to={newEntryPath(entityId)}
        >
          <AddIcon />
          新規エントリを作成
        </Fab>
      </Box>

      {/* This box shows each entry Cards */}
      <Grid container spacing={2}>
        {displayedEntries.map((entry) => {
          return (
            <Grid item xs={4} key={entry.id}>
              <Card sx={{ height: "100%" }}>
                <CardHeader
                  sx={{
                    p: "0px",
                    mt: "24px",
                    mx: "16px",
                    mb: "16px",
                  }}
                  title={
                    <CardActionArea
                      component={Link}
                      to={entryDetailsPath(entityId, entry.id)}
                    >
                      <Typography variant="h6">{entry.name}</Typography>
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
              </Card>
            </Grid>
          );
        })}
      </Grid>
      <Box display="flex" justifyContent="center" my="30px">
        <Stack spacing={2}>
          <Pagination
            count={totalPageCount}
            page={page}
            onChange={handleChange}
            color="primary"
          />
        </Stack>
      </Box>
    </Box>
  );
};
