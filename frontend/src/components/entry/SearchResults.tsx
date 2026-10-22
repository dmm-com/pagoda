import {
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchResult,
  AdvancedSearchSort,
  EntityAttrIDandName,
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
import { FC, useMemo } from "react";
import { Link } from "react-router";

import { SearchResultsTableHead } from "./SearchResultsTableHead";
import { useJoinedAttributeRowHeights } from "./useJoinedAttributeRowHeights";

import { AironeLink } from "components/common";
import { PaginationFooter } from "components/common/PaginationFooter";
import {
  AttributeValue,
  AttributeValueList,
  AttributeValueListItem,
} from "components/entry/AttributeValue";
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
  defaultReferralIncludeModelIds?: number[];
  defaultReferralExcludeModelIds?: number[];
  defaultAttrsFilter?: AttrsFilter;
  defaultSort?: AdvancedSearchSort;
  bulkOperationEntryIds: Array<number>;
  setBulkOperationEntryIds: (entryIds: Array<number>) => void;
  entityIds: number[];
  searchAllEntities: boolean;
  joinAttrs: AdvancedSearchJoinAttrInfo[];
  disablePaginationFooter: boolean;
  isReadonly?: boolean;
  isNarrowDown?: boolean;
  omitHeadline?: boolean;
  entityAttrs: EntityAttrIDandName[];
}

export const SearchResults: FC<Props> = ({
  results,
  page,
  changePage,
  hasReferral,
  defaultEntryFilter,
  defaultReferralFilter,
  defaultReferralIncludeModelIds,
  defaultReferralExcludeModelIds,
  defaultAttrsFilter = {},
  defaultSort,
  bulkOperationEntryIds,
  setBulkOperationEntryIds,
  entityIds,
  searchAllEntities,
  joinAttrs,
  disablePaginationFooter,
  isReadonly = false,
  isNarrowDown = true,
  omitHeadline = false,
  entityAttrs = [],
}) => {
  // attrTypes are sourced from entityAttrs (the EntityAttr definitions),
  // which always include freshly-added attributes regardless of whether any
  // Entry/ES document references them yet. Falling back to results.values[0]
  // covers join attrs ("parent.child") that entityAttrs does not enumerate.
  // (Issue #3449: the previous row-0-only lookup returned undefined for any
  // attribute added after the existing entries were last indexed, which
  // bubbled into AttributeValueField as type=0 and threw.)
  const [attrNames, attrTypes] = useMemo(() => {
    const _attrNames = Object.keys(defaultAttrsFilter);
    const _attrTypes = Object.fromEntries(
      _attrNames.map((attrName) => [
        attrName,
        entityAttrs.find((a) => a.name === attrName)?.type ??
          results.values[0]?.attrs[attrName]?.type ??
          results.values.find(
            (result) => result.joinedAttrs?.[attrName]?.values.length,
          )?.joinedAttrs?.[attrName]?.values[0]?.type,
      ]),
    );
    return [_attrNames, _attrTypes];
  }, [defaultAttrsFilter, results.values, entityAttrs]);

  const joinedAttrSources = useMemo(
    () => ({
      ...Object.fromEntries(
        Object.entries(defaultAttrsFilter)
          .filter(([, filter]) => filter.baseAttrname != null)
          .map(([name, filter]) => [name, filter.baseAttrname!]),
      ),
      ...Object.fromEntries(
        joinAttrs.flatMap((join) =>
          join.attrinfo.map((attr) => [`${join.name}.${attr.name}`, join.name]),
        ),
      ),
    }),
    [defaultAttrsFilter, joinAttrs],
  );
  const arraySourceNames = new Set(Object.values(joinedAttrSources));
  const bodyRef = useJoinedAttributeRowHeights(
    results,
    attrNames,
    joinedAttrSources,
  );

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
              entityAttrs={entityAttrs}
              hasReferral={hasReferral}
              attrTypes={attrTypes}
              defaultEntryFilter={defaultEntryFilter}
              defaultReferralFilter={defaultReferralFilter}
              defaultReferralIncludeModelIds={defaultReferralIncludeModelIds}
              defaultReferralExcludeModelIds={defaultReferralExcludeModelIds}
              defaultAttrsFilter={defaultAttrsFilter}
              defaultSort={defaultSort}
              entityIds={entityIds}
              searchAllEntities={searchAllEntities}
              joinAttrs={joinAttrs}
              handleChangeAllBulkOperationEntryIds={
                handleChangeAllBulkOperationEntryIds
              }
              isReadonly={isReadonly}
              isNarrowDown={isNarrowDown}
              omitHeadline={omitHeadline}
              totalCount={results.count}
            />
            <TableBody ref={bodyRef}>
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
                    <TableCell
                      key={attrName}
                      data-search-attribute={attrName}
                      sx={
                        result.joinedAttrs?.[attrName] != null ||
                        joinedAttrSources[attrName] != null ||
                        arraySourceNames.has(attrName)
                          ? { verticalAlign: "top" }
                          : undefined
                      }
                    >
                      {(() => {
                        const joined = result.joinedAttrs?.[attrName]?.values;
                        const baseAttrName = joinedAttrSources[attrName];
                        const source = baseAttrName
                          ? result.attrs[baseAttrName]?.value
                          : undefined;
                        const sourceLength =
                          source?.asArrayObject?.length ??
                          source?.asArrayNamedObject?.length ??
                          source?.asArrayGroup?.length ??
                          source?.asArrayRole?.length ??
                          0;
                        if (joined != null || sourceLength > 0) {
                          return (
                            <AttributeValueList
                              data-source-attribute={baseAttrName}
                            >
                              {Array.from(
                                {
                                  length: Math.max(
                                    joined?.length ?? 0,
                                    sourceLength,
                                  ),
                                },
                                (_, index) => {
                                  const info = joined?.[index];
                                  return (
                                    <AttributeValueListItem
                                      key={index}
                                      sx={{ boxSizing: "border-box" }}
                                    >
                                      <Box
                                        sx={{
                                          width: "100%",
                                          minHeight: 0,
                                          maxHeight: "100%",
                                          overflowY: "auto",
                                          "& > .MuiList-root > .MuiListItem-root":
                                            {
                                              padding: 0,
                                            },
                                        }}
                                      >
                                        {info == null ? (
                                          "\u00a0"
                                        ) : info.isReadable ? (
                                          <AttributeValue attrInfo={info} />
                                        ) : (
                                          <Typography>
                                            Permission denied.
                                          </Typography>
                                        )}
                                      </Box>
                                    </AttributeValueListItem>
                                  );
                                },
                              )}
                            </AttributeValueList>
                          );
                        }
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
                        return null;
                      })()}
                    </TableCell>
                  ))}
                  {hasReferral && (
                    <TableCell>
                      <List>
                        {result.referrals
                          ?.filter(
                            (referral) =>
                              !defaultReferralIncludeModelIds?.length ||
                              defaultReferralIncludeModelIds?.includes(
                                referral.schema.id,
                              ),
                          )
                          .map((referral) => (
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
            count={results.totalCount ?? results.count}
            maxRowCount={AdvancedSerarchResultListParam.MAX_ROW_COUNT}
            page={page}
            changePage={changePage}
          />
        )}
      </StyledBox>
    </Box>
  );
};
