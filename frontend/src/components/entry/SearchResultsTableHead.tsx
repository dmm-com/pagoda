import {
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchSort,
  AdvancedSearchSortOrderEnum,
  EntityAttrIDandName,
  EntryAttributeTypeTypeEnum,
  EntryHint,
  EntryHintFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import CheckBoxOutlineBlankOutlinedIcon from "@mui/icons-material/CheckBoxOutlineBlankOutlined";
import CheckBoxOutlinedIcon from "@mui/icons-material/CheckBoxOutlined";
import FilterAltIcon from "@mui/icons-material/FilterAlt";
import FilterListIcon from "@mui/icons-material/FilterList";
import {
  Box,
  IconButton,
  TableCell,
  TableHead,
  TableRow,
  TableSortLabel,
  Tooltip,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import {
  ChangeEvent,
  FC,
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useState,
} from "react";
import { useLocation, useNavigate } from "react-router";

import { AdvancedSearchEditModal } from "./AdvancedSearchEditModal";
import { AdvancedSearchJoinModal } from "./AdvancedSearchJoinModal";
import { SearchResultControlMenu } from "./SearchResultControlMenu";
import { SearchResultControlMenuForEntry } from "./SearchResultControlMenuForEntry";
import { SearchResultControlMenuForReferral } from "./SearchResultControlMenuForReferral";

import { getIsFiltered } from "pages/AdvancedSearchResultsPage";
import {
  AttrFilter,
  AttrsFilter,
  ENTRY_NAME_SORT_TARGET,
  formatAdvancedSearchParams,
} from "services/entry/AdvancedSearch";

// Bitmask matching backend airone.lib.types.is_sortable_attr_type:
// STRING/TEXT/OBJECT/GROUP/ROLE/DATE/DATETIME, excluding _ARRAY/_NAMED variants
// and NUMBER/BOOLEAN (which lack a sort-friendly representation in ES today).
const SORTABLE_BASE_MASK =
  EntryAttributeTypeTypeEnum.STRING |
  EntryAttributeTypeTypeEnum.TEXT |
  EntryAttributeTypeTypeEnum.OBJECT |
  EntryAttributeTypeTypeEnum.GROUP |
  EntryAttributeTypeTypeEnum.ROLE |
  EntryAttributeTypeTypeEnum.DATE |
  EntryAttributeTypeTypeEnum.DATETIME;

const isSortableAttrType = (attrType: number | undefined): boolean => {
  if (attrType == null) return false;
  if (
    (attrType &
      (EntryAttributeTypeTypeEnum._ARRAY |
        EntryAttributeTypeTypeEnum._NAMED)) !==
    0
  ) {
    return false;
  }
  if (
    (attrType &
      (EntryAttributeTypeTypeEnum.NUMBER |
        EntryAttributeTypeTypeEnum.BOOLEAN)) !==
    0
  ) {
    return false;
  }
  return (attrType & SORTABLE_BASE_MASK) !== 0;
};

const HeaderBox = styled(Box)({
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
});

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  color: theme.palette.primary.contrastText,
}));

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  color: theme.palette.primary.contrastText,
  minWidth: "300px",
}));

interface Props {
  hasReferral: boolean;
  attrTypes: Record<string, number>;
  defaultEntryFilter?: EntryHint;
  defaultReferralFilter?: string;
  defaultReferralIncludeModelIds?: number[];
  defaultReferralExcludeModelIds?: number[];
  defaultAttrsFilter?: AttrsFilter;
  defaultSort?: AdvancedSearchSort;
  entityIds: number[];
  searchAllEntities: boolean;
  joinAttrs: AdvancedSearchJoinAttrInfo[];
  handleChangeAllBulkOperationEntryIds: (checked: boolean) => void;
  isReadonly?: boolean;
  isNarrowDown?: boolean;
  omitHeadline?: boolean;
  entityAttrs: EntityAttrIDandName[];
  totalCount: number;
}

export interface handleSelectFilterConditionsParams {
  attrFilter?: AttrFilter;
  overwriteReferral?: string;
  overwriteReferralIncludeModelIds?: string[];
  overwriteReferralExcludeModelIds?: string[];
  overwriteHintEntry?: EntryHint;
}

export const SearchResultsTableHead: FC<Props> = ({
  hasReferral,
  attrTypes,
  defaultEntryFilter,
  defaultReferralFilter,
  defaultReferralIncludeModelIds,
  defaultReferralExcludeModelIds,
  defaultAttrsFilter = {},
  defaultSort,
  entityIds,
  searchAllEntities,
  joinAttrs,
  handleChangeAllBulkOperationEntryIds,
  isReadonly = false,
  isNarrowDown = true,
  omitHeadline = false,
  entityAttrs = [],
  totalCount,
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [checked, setChecked] = useState(false);

  /* These are used for AdvancedSearchEditModal component */
  const [openEditModal, setOpenEditModal] = useState(false);
  const [editTargetAttrID, setEditTargetAttrID] = useState(0);
  const [editTargetAttrname, setEditTargetAttrname] = useState("");
  const [editTargetAttrtype, setEditTargetAttrtype] = useState(0);

  const [hintEntry, setHintEntry] = useState<EntryHint>(
    defaultEntryFilter ?? {
      filterKey: EntryHintFilterKeyEnum.CLEARED,
      keyword: "",
    },
  );
  const [entryMenuEls, setEntryMenuEls] = useState<HTMLButtonElement | null>(
    null,
  );

  const hintEntryDispatcher = useCallback((update: Partial<EntryHint>) => {
    setHintEntry((prev) => ({ ...prev, ...update }));
  }, []);

  const [referralFilter, referralFilterDispatcher] = useReducer(
    (
      _state: string,
      event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>,
    ) => event.target.value,
    defaultReferralFilter ?? "",
  );
  const [referralIncludeModelIds, referralIncludeModelIdsDispatcher] =
    useReducer(
      (_state: Array<number>, value: Array<number>) => value,
      defaultReferralIncludeModelIds ?? [],
    );
  const [referralExcludeModelIds, referralExcludeModelIdsDispatcher] =
    useReducer(
      (_state: Array<number>, value: Array<number>) => value,
      defaultReferralExcludeModelIds ?? [],
    );
  const [attrsFilter, setAttrsFilter] = useState<AttrsFilter>(
    defaultAttrsFilter ?? {},
  );

  const [joinAttrName, setJoinAttrname] = useState<string>("");
  const [attributeMenuEls, setAttributeMenuEls] = useState<{
    [key: string]: HTMLButtonElement | null;
  }>({});
  const [referralMenuEls, setReferralMenuEls] =
    useState<HTMLButtonElement | null>(null);

  const attrNames = useMemo(() => {
    return Object.keys(defaultAttrsFilter);
  }, [defaultAttrsFilter]);

  const isFiltered = useMemo(
    (): Record<string, boolean> =>
      Object.fromEntries(
        Object.keys(defaultAttrsFilter ?? {}).map((attrName: string) => {
          const attrFilter = defaultAttrsFilter[attrName];
          return [
            attrName,
            getIsFiltered(attrFilter.filterKey, attrFilter.keyword),
          ];
        }),
      ),
    [defaultAttrsFilter],
  );

  useEffect(() => {
    setAttrsFilter(defaultAttrsFilter ?? {});
  }, [defaultAttrsFilter]);

  const handleSelectFilterConditions =
    (attrName?: string) =>
    ({
      attrFilter,
      overwriteReferral,
      overwriteReferralIncludeModelIds,
      overwriteReferralExcludeModelIds,
      overwriteHintEntry,
    }: handleSelectFilterConditionsParams) => {
      const _attrsFilter =
        attrName != null && attrFilter != null
          ? { ...attrsFilter, [attrName]: attrFilter }
          : attrsFilter;

      const effectiveHintEntry = overwriteHintEntry ?? hintEntry;
      const hintEntryParam =
        effectiveHintEntry.keyword && effectiveHintEntry.keyword.length > 0
          ? {
              filterKey: effectiveHintEntry.filterKey,
              keyword: effectiveHintEntry.keyword,
            }
          : undefined;

      const newParams = formatAdvancedSearchParams({
        attrsFilter: Object.keys(_attrsFilter)
          .filter((k) => _attrsFilter[k]?.joinedAttrname === undefined)
          .reduce((a, k) => ({ ...a, [k]: _attrsFilter[k] }), {}),
        referralName: overwriteReferral ?? referralFilter,
        referralIncludeModelIds:
          overwriteReferralIncludeModelIds ??
          referralIncludeModelIds.map(String),
        referralExcludeModelIds:
          overwriteReferralExcludeModelIds ??
          referralExcludeModelIds.map(String),
        hintEntry: hintEntryParam,
        baseParams: new URLSearchParams(location.search),
        joinAttrs: Object.keys(_attrsFilter)
          .filter((k) => _attrsFilter[k]?.joinedAttrname !== undefined)
          .map((k) => ({
            name: _attrsFilter[k]?.baseAttrname ?? "",
            attrinfo: Object.keys(_attrsFilter)
              .filter(
                (j) =>
                  _attrsFilter[j].baseAttrname === _attrsFilter[k].baseAttrname,
              )
              .map((j) => ({
                name: _attrsFilter[j]?.joinedAttrname ?? "",
                filterKey: _attrsFilter[j].filterKey,
                keyword: _attrsFilter[j].keyword,
              })),
          }))
          // This removes duplicates
          .filter((v, i, a) => a.findIndex((t) => t.name === v.name) === i),
      });

      // simply reload with the new params
      navigate({
        pathname: location.pathname,
        search: "?" + newParams.toString(),
      });
    };

  const handleUpdateAttrFilter =
    (attrName: string) => (attrFilter: AttrFilter) => {
      setAttrsFilter((attrsFilter) => ({
        ...attrsFilter,
        [attrName]: attrFilter,
      }));
    };

  const handleSort = (targetAttrname: string) => {
    let nextOrder: AdvancedSearchSortOrderEnum =
      AdvancedSearchSortOrderEnum.Asc;
    if (defaultSort?.targetAttrname === targetAttrname) {
      nextOrder =
        defaultSort.order === AdvancedSearchSortOrderEnum.Asc
          ? AdvancedSearchSortOrderEnum.Desc
          : AdvancedSearchSortOrderEnum.Asc;
    }
    const newParams = formatAdvancedSearchParams({
      baseParams: new URLSearchParams(location.search),
      sort: { targetAttrname, order: nextOrder },
    });
    navigate({
      pathname: location.pathname,
      search: "?" + newParams.toString(),
    });
  };

  const getSortDirection = (
    targetAttrname: string,
  ): "asc" | "desc" | undefined => {
    if (defaultSort?.targetAttrname !== targetAttrname) return undefined;
    return defaultSort.order === AdvancedSearchSortOrderEnum.Desc
      ? "desc"
      : "asc";
  };

  return (
    <TableHead>
      <TableRow sx={{ backgroundColor: "primary.dark" }}>
        {/* Bulk operation checkbox would be invisible when Readonly mode is true */}
        {!isReadonly && (
          <TableCell sx={{ witdh: "80px" }}>
            <StyledIconButton
              onClick={() => {
                setChecked(!checked);
                handleChangeAllBulkOperationEntryIds(!checked);
              }}
            >
              {checked ? (
                <CheckBoxOutlinedIcon />
              ) : (
                <CheckBoxOutlineBlankOutlinedIcon />
              )}
            </StyledIconButton>
          </TableCell>
        )}

        <StyledTableCell
          {...(omitHeadline
            ? { sx: { minWidth: "0px" } }
            : { sx: { outline: "1px solid #FFFFFF" } })}
        >
          <HeaderBox>
            {omitHeadline ? (
              <Typography />
            ) : (
              <TableSortLabel
                active={defaultSort?.targetAttrname === ENTRY_NAME_SORT_TARGET}
                direction={getSortDirection(ENTRY_NAME_SORT_TARGET) ?? "asc"}
                onClick={() => handleSort(ENTRY_NAME_SORT_TARGET)}
                sx={{
                  color: "primary.contrastText",
                  "&:hover, &.Mui-active, &.Mui-active .MuiTableSortLabel-icon":
                    {
                      color: "primary.contrastText",
                    },
                }}
              >
                <Typography>アイテム名</Typography>
              </TableSortLabel>
            )}

            {/* SearchControlMenu would be invisible when NarrowDown Mode is True */}
            {isNarrowDown && !omitHeadline && (
              <>
                <Tooltip title="アイテム名でフィルタ">
                  <StyledIconButton
                    onClick={(e) => {
                      setEntryMenuEls(e.currentTarget);
                    }}
                  >
                    {hintEntry.keyword ? <FilterAltIcon /> : <FilterListIcon />}
                  </StyledIconButton>
                </Tooltip>
                <SearchResultControlMenuForEntry
                  hintEntry={hintEntry}
                  anchorElem={entryMenuEls}
                  handleClose={() => setEntryMenuEls(null)}
                  hintEntryDispatcher={hintEntryDispatcher}
                  handleSelectFilterConditions={handleSelectFilterConditions()}
                />
              </>
            )}
          </HeaderBox>
        </StyledTableCell>

        {attrNames.map((attrName) => (
          <StyledTableCell key={attrName}>
            <HeaderBox>
              {isSortableAttrType(attrTypes[attrName]) &&
              defaultAttrsFilter[attrName]?.joinedAttrname === undefined ? (
                <TableSortLabel
                  active={defaultSort?.targetAttrname === attrName}
                  direction={getSortDirection(attrName) ?? "asc"}
                  onClick={() => handleSort(attrName)}
                  sx={{
                    color: "primary.contrastText",
                    "&:hover, &.Mui-active, &.Mui-active .MuiTableSortLabel-icon":
                      {
                        color: "primary.contrastText",
                      },
                  }}
                >
                  <Typography>
                    {defaultAttrsFilter[attrName]?.alterName
                      ? defaultAttrsFilter[attrName].alterName
                      : attrName}
                  </Typography>
                </TableSortLabel>
              ) : (
                <Typography>
                  {defaultAttrsFilter[attrName]?.alterName
                    ? defaultAttrsFilter[attrName].alterName
                    : attrName}
                </Typography>
              )}

              {/* Bulk operation checkbox would be invisible when NarrowDown mode is true */}
              {(attrTypes[attrName] & EntryAttributeTypeTypeEnum.OBJECT) > 0 &&
                isNarrowDown &&
                attrsFilter[attrName]?.joinedAttrname === undefined && (
                  <Tooltip title="アイテムの属性を結合する">
                    <StyledIconButton onClick={() => setJoinAttrname(attrName)}>
                      <AddIcon />
                    </StyledIconButton>
                  </Tooltip>
                )}
              {attrName === joinAttrName && (
                <AdvancedSearchJoinModal
                  targetEntityIds={entityIds}
                  searchAllEntities={searchAllEntities}
                  targetAttrname={joinAttrName}
                  joinAttrs={joinAttrs}
                  handleClose={() => setJoinAttrname("")}
                />
              )}
              {isNarrowDown && (
                <>
                  <Tooltip title="属性値でフィルタ">
                    <StyledIconButton
                      onClick={(e) => {
                        setAttributeMenuEls({
                          ...attributeMenuEls,
                          [attrName]: e.currentTarget,
                        });
                      }}
                      sx={{ marginLeft: "auto" }}
                    >
                      {(isFiltered[attrName] ?? false) ? (
                        <FilterAltIcon />
                      ) : (
                        <FilterListIcon />
                      )}
                    </StyledIconButton>
                  </Tooltip>
                  <SearchResultControlMenu
                    attrname={attrName}
                    attrFilter={attrsFilter[attrName]}
                    anchorElem={attributeMenuEls[attrName]}
                    handleClose={() =>
                      setAttributeMenuEls({
                        ...attributeMenuEls,
                        [attrName]: null,
                      })
                    }
                    handleSelectFilterConditions={handleSelectFilterConditions(
                      attrName,
                    )}
                    handleUpdateAttrFilter={handleUpdateAttrFilter(attrName)}
                    attrType={attrTypes[attrName]}
                    setOpenEditModal={setOpenEditModal}
                    isDisabledEditModal={
                      searchAllEntities || joinAttrs.length > 0
                    }
                    entityAttrs={entityAttrs}
                    setEditTargetAttrID={setEditTargetAttrID}
                    setEditTargetAttrname={setEditTargetAttrname}
                    setEditTargetAttrtype={setEditTargetAttrtype}
                    totalCount={totalCount}
                  />
                </>
              )}
            </HeaderBox>
          </StyledTableCell>
        ))}
        {hasReferral && (
          <StyledTableCell sx={{ outline: "1px solid #FFFFFF" }}>
            <HeaderBox>
              <Typography>参照アイテム</Typography>
              <Tooltip title="参照アイテムでフィルタ">
                <StyledIconButton
                  onClick={(e) => {
                    setReferralMenuEls(e.currentTarget);
                  }}
                >
                  {defaultReferralFilter ||
                  defaultReferralIncludeModelIds?.length ||
                  defaultReferralExcludeModelIds?.length ? (
                    <FilterAltIcon />
                  ) : (
                    <FilterListIcon />
                  )}
                </StyledIconButton>
              </Tooltip>
              <SearchResultControlMenuForReferral
                referralFilter={referralFilter}
                referralIncludeModelIds={referralIncludeModelIds}
                referralExcludeModelIds={referralExcludeModelIds}
                anchorElem={referralMenuEls}
                handleClose={() => setReferralMenuEls(null)}
                referralFilterDispatcher={referralFilterDispatcher}
                referralIncludeModelIdsDispatcher={
                  referralIncludeModelIdsDispatcher
                }
                referralExcludeModelIdsDispatcher={
                  referralExcludeModelIdsDispatcher
                }
                handleSelectFilterConditions={handleSelectFilterConditions()}
              />
            </HeaderBox>
          </StyledTableCell>
        )}
      </TableRow>

      <AdvancedSearchEditModal
        openModal={openEditModal}
        handleClose={() => {
          setOpenEditModal(false);
          if (editTargetAttrname) {
            setAttributeMenuEls({
              ...attributeMenuEls,
              [editTargetAttrname]: null,
            });
          }
        }}
        modelIds={entityIds}
        attrsFilter={attrsFilter}
        targetAttrID={editTargetAttrID}
        targetAttrname={editTargetAttrname}
        targetAttrtype={editTargetAttrtype}
      ></AdvancedSearchEditModal>
    </TableHead>
  );
};
