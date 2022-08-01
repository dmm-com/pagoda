import SearchIcon from "@mui/icons-material/Search";
import {
  InputAdornment,
  TableCell,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useReducer } from "react";
import { useHistory, useLocation } from "react-router-dom";

import { PaginatedTable } from "components/common/PaginatedTable";
import { AttributeValue } from "components/entry/AttributeValue";

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#F9FAFA",
  },
  "&:nth-of-type(even)": {
    backgroundColor: "#FFFFFF",
  },
  "&:last-child td, &:last-child th": {
    border: 0,
  },
}));

interface Props {
  results: {
    attrs: Map<string, { type: number; value: any }>;
    entry: {
      name: string;
    };
    referrals: {
      id: number;
      name: string;
      schema: string;
    }[];
  }[];
  defaultEntryFilter?: string;
  defaultReferralFilter?: string;
  defaultAttrsFilter?: any;
}

export const SearchResults: FC<Props> = ({
  results,
  defaultEntryFilter,
  defaultReferralFilter,
  defaultAttrsFilter,
}) => {
  const location = useLocation();
  const history = useHistory();

  const [entryFilter, entryFilterDispatcher] = useReducer((_, event) => {
    return event.target.value;
  }, defaultEntryFilter ?? "");
  const [referralFilter, referralFilterDispatcher] = useReducer((_, event) => {
    return event.target.value;
  }, defaultReferralFilter ?? "");
  const [attrsFilter, attrsFilterDispatcher] = useReducer(
    (state, { event, name }) => {
      return { ...state, [name]: event.target.value };
    },
    defaultAttrsFilter ?? []
  );

  const attrNames = results.length > 0 ? Object.keys(results[0].attrs) : [];
  const hasReferral = results.length > 0 ? results[0].referrals : false;

  const handleKeyPress = (event) => {
    if (event.key === "Enter") {
      const params = new URLSearchParams(location.search);
      params.set("entry_name", entryFilter);
      params.set("referral_name", referralFilter);
      params.set(
        "attrinfo",
        JSON.stringify(
          Object.keys(attrsFilter).map((key) => {
            return { name: key, keyword: attrsFilter[key] };
          })
        )
      );

      // simply reload with the new params
      history.push({
        pathname: location.pathname,
        search: "?" + params.toString(),
      });
      history.go(0);
    }
  };

  return (
    <PaginatedTable
      rows={results}
      tableHeadRow={
        <TableRow sx={{ backgroundColor: "primary.dark" }}>
          {/* FIXME avoid overlapping elements when scrolling */}
          <TableCell
            sx={{
              color: "primary.contrastText",
              minWidth: "300px",
              position: "sticky",
              left: 0,
              zIndex: 1,
              backgroundColor: "inherit",
              outline: "1px solid #FFFFFF",
            }}
          >
            <Typography>エントリ名</Typography>
            <TextField
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ color: "white" }} />
                  </InputAdornment>
                ),
                sx: {
                  color: "#FFFFFF",
                  "&.Mui-focused": {
                    background: "#00000061",
                  },
                },
              }}
              inputProps={{
                style: {
                  padding: "8px 0 8px 4px",
                },
              }}
              sx={{
                background: "#0000001F",
                margin: "8px 0",
              }}
              defaultValue={defaultEntryFilter}
              onChange={entryFilterDispatcher}
              onKeyPress={handleKeyPress}
            />
          </TableCell>
          {Object.keys(attrsFilter).map((attrName) => (
            <TableCell
              sx={{ color: "primary.contrastText", minWidth: "300px" }}
              key={attrName}
            >
              <Typography>{attrName}</Typography>
              <TextField
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon sx={{ color: "white" }} />
                    </InputAdornment>
                  ),
                  sx: {
                    color: "#FFFFFF",
                    "&.Mui-focused": {
                      background: "#00000061",
                    },
                  },
                }}
                inputProps={{
                  style: {
                    padding: "8px 0 8px 4px",
                  },
                }}
                sx={{
                  background: "#0000001F",
                  margin: "8px 0",
                }}
                defaultValue={defaultAttrsFilter[attrName] || ""}
                onChange={(e) =>
                  attrsFilterDispatcher({ event: e, name: attrName })
                }
                onKeyPress={handleKeyPress}
              />
            </TableCell>
          ))}
          {hasReferral && (
            <TableCell
              sx={{ color: "primary.contrastText", minWidth: "300px" }}
            >
              <Typography>参照エントリ</Typography>
              <TextField
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon sx={{ color: "white" }} />
                    </InputAdornment>
                  ),
                  sx: {
                    color: "#FFFFFF",
                    "&.Mui-focused": {
                      background: "#00000061",
                    },
                  },
                }}
                inputProps={{
                  style: {
                    padding: "8px 0 8px 4px",
                  },
                }}
                sx={{
                  background: "#0000001F",
                  margin: "8px 0",
                }}
                defaultValue={defaultReferralFilter}
                onChange={referralFilterDispatcher}
                onKeyPress={handleKeyPress}
              />
            </TableCell>
          )}
        </TableRow>
      }
      tableBodyRowGenerator={(result, index) => (
        <StyledTableRow key={index}>
          {/* FIXME avoid overlapping elements when scrolling */}
          <TableCell
            sx={{
              backgroundColor: "inherit",
              minWidth: "300px",
              position: "sticky",
              left: 0,
              zIndex: 1,
            }}
          >
            <Typography>{result.entry.name}</Typography>
          </TableCell>
          {Object.keys(attrsFilter).map((attrName) => (
            <TableCell sx={{ minWidth: "300px" }} key={attrName}>
              {result.attrs[attrName] && (
                <AttributeValue attrInfo={result.attrs[attrName]} />
              )}
            </TableCell>
          ))}
          {hasReferral && (
            <TableCell sx={{ minWidth: "300px" }}>
              {result.referrals.map((referral) => {
                return (
                  <Typography key={referral.id}>{referral.name}</Typography>
                );
              })}
            </TableCell>
          )}
        </StyledTableRow>
      )}
      rowsPerPageOptions={[100, 250, 1000]}
    />
  );
};
