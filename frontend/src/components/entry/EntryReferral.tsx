import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Pagination,
  Stack,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useAsyncWithThrow } from "../../hooks/useAsyncWithThrow";
import { usePage } from "../../hooks/usePage";
import { aironeApiClient } from "../../repository/AironeApiClient";
import { EntryReferralList } from "../../services/Constants";
import { normalizeToMatch } from "../../services/StringUtil";

import { entryDetailsPath } from "Routes";
import { SearchBox } from "components/common/SearchBox";

const ReferralCount = styled(Typography)(({}) => ({
  fontSize: "16px",
  fontWeight: "Medium",
  pb: "16px",
}));

const StyledListItem = styled(ListItem)(({}) => ({
  "&:first-of-type": {
    borderTop: "1px solid",
    borderTopColor: "divider",
  },
}));

interface Props {
  entryId: number;
}

export const EntryReferral: FC<Props> = ({ entryId }) => {
  const [page, changePage] = usePage();

  const [keyword, setKeyword] = useState("");
  const [keywordQuery, setKeywordQuery] = useState("");

  const referredEntries = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntryReferral(
      entryId,
      page,
      keywordQuery !== "" ? keywordQuery : undefined
    );
  }, [entryId, page, keywordQuery]);

  const [matchedEntries, count, maxPage] = useMemo(() => {
    if (!referredEntries.loading && referredEntries.value != null) {
      return [
        referredEntries.value.results,
        referredEntries.value.count,
        Math.ceil(
          (referredEntries.value.count ?? 0) / EntryReferralList.MAX_ROW_COUNT
        ),
      ];
    }
    return [[], 0, 0];
  }, [referredEntries.loading]);

  return (
    <Box>
      <Box px="16px">
        <ReferralCount id="ref_count">
          {"関連づけられたアイテム(計" + count + ")"}
        </ReferralCount>
        <SearchBox
          placeholder="アイテムを絞り込む"
          value={keyword}
          onChange={(e) => {
            setKeyword(e.target.value);
          }}
          onKeyPress={(e) => {
            if (e.key === "Enter") {
              changePage(1);
              setKeywordQuery(
                keyword.length > 0 ? normalizeToMatch(keyword) : ""
              );
            }
          }}
        />
      </Box>
      <Box display="flex" justifyContent="center" my="24px">
        <Stack spacing={2}>
          <Pagination
            id="ref_page"
            siblingCount={0}
            boundaryCount={1}
            count={maxPage}
            page={page}
            onChange={(e, page) => changePage(page)}
            color="primary"
          />
        </Stack>
      </Box>
      <List id="ref_list" sx={{ py: "8px" }}>
        {matchedEntries?.map((entry) => (
          <StyledListItem key={entry.id} divider={true} disablePadding>
            <ListItemButton
              component={Link}
              to={entryDetailsPath(entry.schema?.id ?? 0, entry.id)}
            >
              <ListItemText sx={{ px: "16px" }}>{entry.name}</ListItemText>
            </ListItemButton>
          </StyledListItem>
        ))}
      </List>
    </Box>
  );
};
