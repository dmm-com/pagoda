import { AdvancedSearchResultAttrInfoFilterKeyEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import FilterAltIcon from "@mui/icons-material/FilterAlt";
import FilterListIcon from "@mui/icons-material/FilterList";
import {
  Box,
  IconButton,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, {
  ChangeEvent,
  FC,
  useMemo,
  useReducer,
  useState,
  Dispatch,
  SetStateAction,
} from "react";
import { useHistory, useLocation } from "react-router-dom";

import {
  AttrFilter,
  AttrsFilter,
  formatAdvancedSearchParams,
} from "../../services/entry/AdvancedSearch";

import { SearchResultControlMenu } from "./SearchResultControlMenu";
import { SearchResultControlMenuForEntry } from "./SearchResultControlMenuForEntry";
import { SearchResultControlMenuForReferral } from "./SearchResultControlMenuForReferral";

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

interface JoiningProps {
  attrType: number;
  attrName: string;
  setJoinAttrname: Dispatch<SetStateAction<string>>;
  unjoinable: boolean;
}

const JoinableAttrHeader: FC<JoiningProps> = ({
  attrType,
  attrName,
  setJoinAttrname,
  unjoinable,
}) => {
  const JoinableBox = styled(Box)({
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
  });

  if (unjoinable) {
    return <Typography>{attrName}</Typography>;
  }

  switch (attrType) {
    case AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY:
      return (
        <JoinableBox>
          <Typography>{attrName}</Typography>
          <StyledIconButton
            onClick={() => {
              setJoinAttrname(attrName);
            }}
          >
            <AddIcon />
          </StyledIconButton>
        </JoinableBox>
      );

    default:
      return <Typography>{attrName}</Typography>;
  }
};

interface Props {
  hasReferral: boolean;
  attrTypes: Record<string, number>;
  defaultEntryFilter?: string;
  defaultReferralFilter?: string;
  defaultAttrsFilter?: AttrsFilter;
  setJoinAttrname: Dispatch<SetStateAction<string>>;
}

export const SearchResultsTableHead: FC<Props> = ({
  hasReferral,
  attrTypes,
  defaultEntryFilter,
  defaultReferralFilter,
  defaultAttrsFilter = {},
  setJoinAttrname,
}) => {
  const location = useLocation();
  const history = useHistory();

  const [entryFilter, entryFilterDispatcher] = useReducer(
    (
      _state: string,
      event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
    ) => event.target.value,
    defaultEntryFilter ?? ""
  );
  const [referralFilter, referralFilterDispatcher] = useReducer(
    (
      _state: string,
      event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
    ) => event.target.value,
    defaultReferralFilter ?? ""
  );
  const [attrsFilter, setAttrsFilter] = useState<AttrsFilter>(
    defaultAttrsFilter ?? {}
  );

  const [attributeMenuEls, setAttributeMenuEls] = useState<{
    [key: string]: HTMLButtonElement | null;
  }>({});
  const [entryMenuEls, setEntryMenuEls] = useState<HTMLButtonElement | null>(
    null
  );
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
          switch (attrFilter?.filterKey) {
            case AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY:
            case AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY:
            case AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED:
              return [attrName, true];
            case AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED:
              return [attrName, attrFilter.keyword !== ""];
            case AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED:
              return [attrName, attrFilter.keyword !== ""];
          }
          return [attrName, false];
        })
      ),
    [defaultAttrsFilter]
  );

  const handleSelectFilterConditions =
    (attrName?: string) =>
    (
      attrFilter?: AttrFilter,
      overwriteEntryName?: string,
      overwriteReferral?: string
    ) => {
      const _attrsFilter =
        attrName != null && attrFilter != null
          ? { ...attrsFilter, [attrName]: attrFilter }
          : attrsFilter;

      const newParams = formatAdvancedSearchParams({
        attrsFilter: Object.keys(_attrsFilter)
          .filter((k) => _attrsFilter[k].joinedAttrname === undefined)
          .reduce((a, k) => ({ ...a, [k]: _attrsFilter[k] }), {}),
        entryName: overwriteEntryName ?? entryFilter,
        referralName: overwriteReferral ?? referralFilter,
        baseParams: new URLSearchParams(location.search),
        joinAttrs: Object.keys(_attrsFilter)
          .filter((k) => _attrsFilter[k].joinedAttrname !== undefined)
          .map((k) => ({
            name: _attrsFilter[k]?.baseAttrname ?? "",
            attrinfo: Object.keys(_attrsFilter)
              .filter(
                (j) =>
                  _attrsFilter[j].baseAttrname === _attrsFilter[k].baseAttrname
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
      history.push({
        pathname: location.pathname,
        search: "?" + newParams.toString(),
      });
      history.go(0);
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
        <TableCell sx={{ witdh: "80px" }} />
        <StyledTableCell sx={{ outline: "1px solid #FFFFFF" }}>
          <HeaderBox>
            <Typography>エントリ名</Typography>
            <StyledIconButton
              onClick={(e) => {
                setEntryMenuEls(e.currentTarget);
              }}
            >
              {defaultEntryFilter ? <FilterAltIcon /> : <FilterListIcon />}
            </StyledIconButton>
            <SearchResultControlMenuForEntry
              entryFilter={entryFilter}
              anchorElem={entryMenuEls}
              handleClose={() => setEntryMenuEls(null)}
              entryFilterDispatcher={entryFilterDispatcher}
              handleSelectFilterConditions={handleSelectFilterConditions()}
              handleClear={() => handleSelectFilterConditions()(undefined, "")}
            />
          </HeaderBox>
        </StyledTableCell>
        {attrNames.map((attrName) => (
          <StyledTableCell key={attrName}>
            <HeaderBox>
              <JoinableAttrHeader
                attrType={attrTypes[attrName]}
                attrName={attrName}
                setJoinAttrname={setJoinAttrname}
                unjoinable={
                  defaultAttrsFilter[attrName].joinedAttrname !== undefined
                }
              />
              <StyledIconButton
                onClick={(e) => {
                  setAttributeMenuEls({
                    ...attributeMenuEls,
                    [attrName]: e.currentTarget,
                  });
                }}
              >
                {isFiltered[attrName] ?? false ? (
                  <FilterAltIcon />
                ) : (
                  <FilterListIcon />
                )}
              </StyledIconButton>
              <SearchResultControlMenu
                attrFilter={attrsFilter[attrName]}
                anchorElem={attributeMenuEls[attrName]}
                handleClose={() =>
                  setAttributeMenuEls({
                    ...attributeMenuEls,
                    [attrName]: null,
                  })
                }
                handleSelectFilterConditions={handleSelectFilterConditions(
                  attrName
                )}
                handleUpdateAttrFilter={handleUpdateAttrFilter(attrName)}
                attrType={attrTypes[attrName]}
              />
            </HeaderBox>
          </StyledTableCell>
        ))}
        {hasReferral && (
          <StyledTableCell sx={{ outline: "1px solid #FFFFFF" }}>
            <HeaderBox>
              <Typography>参照エントリ</Typography>
              <StyledIconButton
                onClick={(e) => {
                  setReferralMenuEls(e.currentTarget);
                }}
              >
                {defaultReferralFilter ? <FilterAltIcon /> : <FilterListIcon />}
              </StyledIconButton>
              <SearchResultControlMenuForReferral
                referralFilter={referralFilter}
                anchorElem={referralMenuEls}
                handleClose={() => setReferralMenuEls(null)}
                referralFilterDispatcher={referralFilterDispatcher}
                handleSelectFilterConditions={handleSelectFilterConditions()}
                handleClear={() =>
                  handleSelectFilterConditions()(undefined, undefined, "")
                }
              />
            </HeaderBox>
          </StyledTableCell>
        )}
      </TableRow>
    </TableHead>
  );
};
