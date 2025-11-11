import {
  AdvancedSearchJoinAttrInfo,
  EntryAttributeTypeTypeEnum,
  EntryHint,
  EntryHintFilterKeyEnum,
  EntityAttrIDandName,
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
  formatAdvancedSearchParams,
} from "services/entry/AdvancedSearch";

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
  defaultAttrsFilter?: AttrsFilter;
  entityIds: number[];
  searchAllEntities: boolean;
  joinAttrs: AdvancedSearchJoinAttrInfo[];
  handleChangeAllBulkOperationEntryIds: (checked: boolean) => void;
  isReadonly?: boolean;
  isNarrowDown?: boolean;
  omitHeadline?: boolean;
  entityAttrs: EntityAttrIDandName[];
}

export const SearchResultsTableHead: FC<Props> = ({
  hasReferral,
  attrTypes,
  defaultEntryFilter,
  defaultReferralFilter,
  defaultAttrsFilter = {},
  entityIds,
  searchAllEntities,
  joinAttrs,
  handleChangeAllBulkOperationEntryIds,
  isReadonly = false,
  isNarrowDown = true,
  omitHeadline = false,
  entityAttrs = [],
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
    (
      attrFilter?: AttrFilter,
      overwriteReferral?: string,
      overwriteHintEntry?: EntryHint,
    ) => {
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
            <Typography>{!omitHeadline ? "アイテム名" : ""}</Typography>

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
              <Typography>
                {defaultAttrsFilter[attrName]?.alterName
                  ? defaultAttrsFilter[attrName].alterName
                  : attrName}
              </Typography>

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
                    entityAttrs={entityAttrs}
                    setEditTargetAttrID={setEditTargetAttrID}
                    setEditTargetAttrname={setEditTargetAttrname}
                    setEditTargetAttrtype={setEditTargetAttrtype}
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
                  {defaultReferralFilter ? (
                    <FilterAltIcon />
                  ) : (
                    <FilterListIcon />
                  )}
                </StyledIconButton>
              </Tooltip>
              <SearchResultControlMenuForReferral
                referralFilter={referralFilter}
                anchorElem={referralMenuEls}
                handleClose={() => setReferralMenuEls(null)}
                referralFilterDispatcher={referralFilterDispatcher}
                handleSelectFilterConditions={(
                  attrFilter,
                  overwriteEntryName,
                  overwriteReferral,
                ) =>
                  handleSelectFilterConditions()(attrFilter, overwriteReferral)
                }
                handleClear={() =>
                  handleSelectFilterConditions()(undefined, "")
                }
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
        attrsFilter={attrsFilter}
        targetAttrID={editTargetAttrID}
        targetAttrname={editTargetAttrname}
        targetAttrtype={editTargetAttrtype}
      ></AdvancedSearchEditModal>
    </TableHead>
  );
};
