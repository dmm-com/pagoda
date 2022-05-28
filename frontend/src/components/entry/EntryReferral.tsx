import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Stack,
  Pagination,
} from "@mui/material";
import React, { FC, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../../apiclient/AironeApiClientV2";
import { EntryReferralList } from "../../utils/Constants";
import { normalizeToMatch } from "../../utils/StringUtil";

import { entryDetailsPath } from "Routes";
import { SearchBox } from "components/common/SearchBox";

interface Props {
  entityId: number;
  entryId: number;
}

export const EntryReferral: FC<Props> = ({ entityId, entryId }) => {
  const params = new URLSearchParams(location.search);

  const [page, setPage] = useState<number>(
    params.has("page") ? Number(params.get("page")) : 1
  );
  const [keyword, setKeyword] = useState("");
  const [keywordQuery, setKeywordQuery] = useState("");

  const referredEntries = useAsync(async () => {
    return await aironeApiClientV2.getEntryReferral(
      entryId,
      page,
      keywordQuery !== "" ? keywordQuery : undefined
    );
  }, [entryId, page, keywordQuery]);

  const [matchedEntries, count, maxPage] = useMemo(() => {
    if (!referredEntries.loading) {
      return [
        referredEntries.value.results,
        referredEntries.value.count,
        Math.ceil(
          referredEntries.value.count / EntryReferralList.MAX_ROW_COUNT
        ),
      ];
    }
    return [[], 0, 0];
  }, [referredEntries.loading]);

  return (
    <Box>
      <Box px="16px">
        <Typography sx={{ fontSize: "16px", fontWeight: "Medium", pb: "16px" }}>
          関連づけられたエントリ(計{count})
        </Typography>
        <SearchBox
          placeholder="エントリを絞り込む"
          value={keyword}
          onChange={(e) => {
            setKeyword(e.target.value);
          }}
          onKeyPress={(e) => {
            if (e.key === "Enter") {
              setKeywordQuery(
                keyword.length > 0 ? normalizeToMatch(keyword) : undefined
              );
            }
          }}
        />
      </Box>
      <Box display="flex" justifyContent="center" my="24px">
        <Stack spacing={2}>
          <Pagination
            count={maxPage}
            page={page}
            onChange={(e, page) => setPage(page)}
            color="primary"
          />
        </Stack>
      </Box>
      <List sx={{ py: "8px" }}>
        {matchedEntries.map((entry) => (
          <ListItem
            key={entry.id}
            divider={true}
            disablePadding
            sx={{
              "&:first-of-type": {
                borderTop: "1px solid",
                borderTopColor: "divider",
              },
            }}
          >
            <ListItemButton
              component={Link}
              to={entryDetailsPath(entityId, entry.id)}
            >
              <ListItemText sx={{ px: "16px" }}>{entry.name}</ListItemText>
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};
