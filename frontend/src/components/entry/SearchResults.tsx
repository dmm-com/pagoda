import {
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchResult,
  EntryHint,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import {
  Box,
  Checkbox,
  IconButton,
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
import { ExtendButtonBaseTypeMap } from "@mui/material/ButtonBase/ButtonBase";
import { IconButtonTypeMap } from "@mui/material/IconButton/IconButton";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import React, { FC, useMemo } from "react";
import { Link } from "react-router";

import { SearchResultsTableHead } from "./SearchResultsTableHead";

import { AironeLink } from "components/common";
import { PaginationFooter } from "components/common/PaginationFooter";
import { AttributeValue } from "components/entry/AttributeValue";
import { entryDetailsPath, entryEditPath } from "routes/Routes";
import { AdvancedSerarchResultListParam } from "services/Constants";
import { AttrsFilter } from "services/entry/AdvancedSearch";

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  margin: theme.spacing(1),
})) as OverridableComponent<ExtendButtonBaseTypeMap<IconButtonTypeMap>>;

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
  defaultEntryFilter?: EntryHint;
  defaultReferralFilter?: string;
  defaultAttrsFilter?: AttrsFilter;
  bulkOperationEntryIds: Array<number>;
  setBulkOperationEntryIds: (entryIds: Array<number>) => void;
  entityIds: number[];
  searchAllEntities: boolean;
  joinAttrs: AdvancedSearchJoinAttrInfo[];
  disablePaginationFooter: boolean;
  isReadonly?: boolean;
  isNarrowDown?: boolean;
  omitHeadline?: boolean;
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
  setBulkOperationEntryIds,
  entityIds,
  searchAllEntities,
  joinAttrs,
  disablePaginationFooter,
  isReadonly = false,
  isNarrowDown = true,
  omitHeadline = false,
}) => {
  // NOTE attrTypes are guessed by the first element on the results. So if it has no appropriate attr,
  // the type guess doesn't work well. We should improve attr type API if more accurate type is needed.
  const [attrNames, attrTypes] = useMemo(() => {
    const _attrNames = Object.keys(defaultAttrsFilter);
    const _attrTypes = Object.fromEntries(
      _attrNames.map((attrName) => [
        attrName,
        results.values[0]?.attrs[attrName]?.type,
      ]),
    );
    return [_attrNames, _attrTypes];
  }, [defaultAttrsFilter, results.values]);

  const handleChangeBulkOperationEntryId = (id: number, checked: boolean) => {
    if (checked) {
      setBulkOperationEntryIds([...bulkOperationEntryIds, id]);
    } else {
      setBulkOperationEntryIds(bulkOperationEntryIds.filter((i) => i !== id));
    }
  };

  const handleChangeAllBulkOperationEntryIds = (checked: boolean) => {
    if (checked) {
      setBulkOperationEntryIds(results.values.map((v) => v.entry.id));
    } else {
      setBulkOperationEntryIds([]);
    }
  };

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
              handleChangeAllBulkOperationEntryIds={
                handleChangeAllBulkOperationEntryIds
              }
              isReadonly={isReadonly}
              isNarrowDown={isNarrowDown}
              omitHeadline={omitHeadline}
            />
            <TableBody>
              {results.values?.map((result) => (
                <StyledTableRow key={result.entry.id}>
                  {/* Bulk operation checkbox would be invisible when Readonly mode is true */}
                  {!isReadonly && (
                    <TableCell sx={{ padding: 0 }}>
                      <Checkbox
                        checked={bulkOperationEntryIds.includes(
                          result.entry.id,
                        )}
                        onChange={(e) =>
                          handleChangeBulkOperationEntryId(
                            result.entry.id,
                            e.target.checked,
                          )
                        }
                      />
                    </TableCell>
                  )}

                  <TableCell>
                    {omitHeadline ? (
                      // show edit icon instead of item name when omitHeadline is true
                      <StyledIconButton
                        component={Link}
                        to={entryEditPath(result.entity.id, result.entry.id)}
                      >
                        <EditOutlinedIcon />
                      </StyledIconButton>
                    ) : (
                      // show each item name
                      <Box
                        component={AironeLink}
                        to={entryDetailsPath(result.entity.id, result.entry.id)}
                      >
                        {result.entry.name}
                      </Box>
                    )}
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
