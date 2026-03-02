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
import { FC, Suspense, useMemo, useState } from "react";
import { Link } from "react-router";

import { usePage } from "../../hooks/usePage";
import { usePagodaSWR } from "../../hooks/usePagodaSWR";
import { aironeApiClient } from "../../repository/AironeApiClient";
import { EntryReferralList } from "../../services/Constants";
import { normalizeToMatch } from "../../services/StringUtil";

import { Loading } from "components/common/Loading";
import { SearchBox } from "components/common/SearchBox";
import { entryDetailsPath } from "routes/Routes";

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

const EntryReferralContent: FC<Props> = ({ entryId }) => {
  const { page, changePage } = usePage();
  const [keywordQuery, setKeywordQuery] = useState("");

  const { data: referredEntries } = usePagodaSWR(
    ["referralEntries", entryId, page, keywordQuery],
    () =>
      aironeApiClient.getEntryReferral(
        entryId,
        page,
        keywordQuery !== "" ? keywordQuery : undefined,
      ),
    { suspense: true },
  );

  const [matchedEntries, count, maxPage] = useMemo(() => {
    return [
      referredEntries.results,
      referredEntries.count,
      Math.ceil((referredEntries.count ?? 0) / EntryReferralList.MAX_ROW_COUNT),
    ];
  }, [referredEntries]);

  return (
    <Box>
      <Box px="16px">
        <ReferralCount id="ref_count">
          {"関連づけられたアイテム(計" + count + ")"}
        </ReferralCount>
        <SearchBox
          placeholder="アイテムを絞り込む"
          onKeyPress={(e) => {
            if (e.key === "Enter") {
              changePage(1);
              setKeywordQuery(
                normalizeToMatch((e.target as HTMLInputElement).value ?? ""),
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

export const EntryReferral: FC<Props> = ({ entryId }) => {
  return (
    <Suspense fallback={<Loading />}>
      <EntryReferralContent entryId={entryId} />
    </Suspense>
  );
};
