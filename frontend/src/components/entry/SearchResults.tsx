import { AdvancedSearchResultValue } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Box,
  Checkbox,
  List,
  ListItem,
  Pagination,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useMemo } from "react";
import { Link } from "react-router-dom";

import { SearchResultsTableHead } from "./SearchResultsTableHead";

import { entryDetailsPath } from "Routes";
import { AttributeValue } from "components/entry/AttributeValue";
import { AttrsFilter } from "services/entry/AdvancedSearch";

const StyledBox = styled(Box)({
  display: "table",
  overflowX: "inherit",
  padding: "24px",
});

const StyledTableRow = styled(TableRow)({
  "&:nth-of-type(odd)": {
    backgroundColor: "#F9FAFA",
  },
  "&:nth-of-type(even)": {
    backgroundColor: "#FFFFFF",
  },
  "&:last-child td, &:last-child th": {
    border: 0,
  },
  "& td": {
    padding: "8px 16px",
  },
});

interface Props {
  results: Array<AdvancedSearchResultValue>;
  page: number;
  maxPage: number;
  hasReferral: boolean;
  handleChangePage: (page: number) => void;
  defaultEntryFilter?: string;
  defaultReferralFilter?: string;
  defaultAttrsFilter?: AttrsFilter;
  bulkOperationEntryIds: Array<number>;
  handleChangeBulkOperationEntryId: (id: number, checked: boolean) => void;
}

export const SearchResults: FC<Props> = ({
  results,
  page,
  maxPage,
  handleChangePage,
  hasReferral,
  defaultEntryFilter,
  defaultReferralFilter,
  defaultAttrsFilter = {},
  bulkOperationEntryIds,
  handleChangeBulkOperationEntryId,
}) => {
  // NOTE attrTypes are guessed by the first element on the results. So if it has no appropriate attr,
  // the type guess doesn't work well. We should improve attr type API if more accurate type is needed.
  const [attrNames, attrTypes] = useMemo(() => {
    const _attrNames = Object.keys(defaultAttrsFilter);
    const _attrTypes = Object.fromEntries(
      _attrNames.map((attrName) => [
        attrName,
        results[0]?.attrs[attrName]?.type,
      ]),
    );
    return [_attrNames, _attrTypes];
  }, [defaultAttrsFilter, results]);

  return (
    <Box display="flex" flexDirection="column">
      <StyledBox>
        <TableContainer component={Paper}>
          <Table id="table_result_list">
            <SearchResultsTableHead
              hasReferral={hasReferral}
              attrTypes={attrTypes}
              defaultEntryFilter={defaultEntryFilter}
              defaultReferralFilter={defaultReferralFilter}
              defaultAttrsFilter={defaultAttrsFilter}
            />
            <TableBody>
              {results.map((result) => (
                <StyledTableRow key={result.entry.id}>
                  <TableCell sx={{ padding: 0 }}>
                    <Checkbox
                      checked={bulkOperationEntryIds.includes(result.entry.id)}
                      onChange={(e) =>
                        handleChangeBulkOperationEntryId(
                          result.entry.id,
                          e.target.checked,
                        )
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Box
                      component={Link}
                      to={entryDetailsPath(result.entity.id, result.entry.id)}
                    >
                      {result.entry.name}
                    </Box>
                  </TableCell>
                  {attrNames.map((attrName) => (
                    <TableCell key={attrName}>
                      {(() => {
                        const info = result.attrs[attrName];
                        if (info != null) {
                          return (
                            <>
                              {info.isReadable ? (
                                <AttributeValue attrInfo={info} />
                              ) : (
                                <Typography>Permission denied.</Typography>
                              )}
                            </>
                          );
                        } else if (!result.isReadable) {
                          return <Typography>Permission denied.</Typography>;
                        }
                      })()}
                    </TableCell>
                  ))}
                  {hasReferral && (
                    <TableCell>
                      <List>
                        {result.referrals?.map((referral) => (
                          <ListItem key={referral.id}>
                            <Box
                              component={Link}
                              to={entryDetailsPath(0, referral.id)}
                            >
                              {referral.name}
                            </Box>
                          </ListItem>
                        ))}
                      </List>
                    </TableCell>
                  )}
                </StyledTableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Box display="flex" justifyContent="center" my="30px">
          <Stack spacing={2}>
            <Pagination
              id="result_page"
              siblingCount={0}
              boundaryCount={1}
              count={maxPage}
              page={page}
              onChange={(e, page) => handleChangePage(page)}
              color="primary"
            />
          </Stack>
        </Box>
      </StyledBox>
    </Box>
  );
};
