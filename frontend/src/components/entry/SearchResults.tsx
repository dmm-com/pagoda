import {
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchResult,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Box,
  Checkbox,
  List,
  ListItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useMemo } from "react";

import { SearchResultsTableHead } from "./SearchResultsTableHead";

import { AironeLink } from "components/common";
import { PaginationFooter } from "components/common/PaginationFooter";
import { AttributeValue } from "components/entry/AttributeValue";
import { entryDetailsPath } from "routes/Routes";
import { AdvancedSerarchResultListParam } from "services/Constants";
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
  results: AdvancedSearchResult;
  page: number;
  changePage: (page: number) => void;
  hasReferral: boolean;
  defaultEntryFilter?: string;
  defaultReferralFilter?: string;
  defaultAttrsFilter?: AttrsFilter;
  bulkOperationEntryIds: Array<number>;
  handleChangeBulkOperationEntryId: (id: number, checked: boolean) => void;
  entityIds: number[];
  searchAllEntities: boolean;
  joinAttrs: AdvancedSearchJoinAttrInfo[];
  disablePaginationFooter: boolean;
  setSearchResults: () => void;
  isReadonly?: boolean;
}

export const SearchResults: FC<Props> = ({
  results,
  page,
  changePage,
  hasReferral,
  defaultEntryFilter,
  defaultReferralFilter,
  defaultAttrsFilter = {},
  bulkOperationEntryIds,
  handleChangeBulkOperationEntryId,
  entityIds,
  searchAllEntities,
  joinAttrs,
  disablePaginationFooter,
  setSearchResults,
  isReadonly = false,
}) => {
  // NOTE attrTypes are guessed by the first element on the results. So if it has no appropriate attr,
  // the type guess doesn't work well. We should improve attr type API if more accurate type is needed.
  const [attrNames, attrTypes] = useMemo(() => {
    const _attrNames = Object.keys(defaultAttrsFilter);
    const _attrTypes = Object.fromEntries(
      _attrNames.map((attrName) => [
        attrName,
        results.values[0]?.attrs[attrName]?.type,
      ])
    );
    return [_attrNames, _attrTypes];
  }, [defaultAttrsFilter, results.values]);

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
              entityIds={entityIds}
              searchAllEntities={searchAllEntities}
              joinAttrs={joinAttrs}
              refreshSearchResults={setSearchResults}
              isReadonly={isReadonly}
            />
            <TableBody>
              {results.values?.map((result) => (
                <StyledTableRow key={result.entry.id}>
                  {/* Bulk operation checkbox would be invisible when Readonly mode is true */}
                  {!isReadonly && (
                    <TableCell sx={{ padding: 0 }}>
                      <Checkbox
                        checked={bulkOperationEntryIds.includes(
                          result.entry.id
                        )}
                        onChange={(e) =>
                          handleChangeBulkOperationEntryId(
                            result.entry.id,
                            e.target.checked
                          )
                        }
                      />
                    </TableCell>
                  )}

                  <TableCell>
                    <Box
                      component={AironeLink}
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
                              component={AironeLink}
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

        {!disablePaginationFooter && (
          <PaginationFooter
            count={results.count}
            maxRowCount={AdvancedSerarchResultListParam.MAX_ROW_COUNT}
            page={page}
            changePage={changePage}
          />
        )}
      </StyledBox>
    </Box>
  );
};
