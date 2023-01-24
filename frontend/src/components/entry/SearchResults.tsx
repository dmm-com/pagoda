import SearchIcon from "@mui/icons-material/Search";
import {
  Box,
  InputAdornment,
  List,
  ListItem,
  Pagination,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useReducer } from "react";
import { useHistory, useLocation, Link } from "react-router-dom";

import { entryDetailsPath } from "Routes";
import { AttributeValue } from "components/entry/AttributeValue";

const StyledBox = styled(Box)({
  margin: "24px",
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
});

interface Props {
  results: {
    attrs: Map<string, { type: number; value: any }>;
    entry: {
      id: number;
      name: string;
    };
    referrals: {
      id: number;
      name: string;
      schema: string;
    }[];
  }[];
  page: number;
  maxPage: number;
  handleChangePage: (page: number) => void;
  defaultEntryFilter?: string;
  defaultReferralFilter?: string;
  defaultAttrsFilter?: { [key: string]: string };
}

export const SearchResults: FC<Props> = ({
  results,
  page,
  maxPage,
  handleChangePage,
  defaultEntryFilter,
  defaultReferralFilter,
  defaultAttrsFilter,
}) => {
  const location = useLocation();
  const history = useHistory();

  const [entryFilter, entryFilterDispatcher] = useReducer(
    (_, event) => event.target.value,
    defaultEntryFilter ?? ""
  );
  const [referralFilter, referralFilterDispatcher] = useReducer(
    (_, event) => event.target.value,
    defaultReferralFilter ?? ""
  );
  const [attrsFilter, attrsFilterDispatcher] = useReducer(
    (state, { event, name }) => ({ ...state, [name]: event.target.value }),
    defaultAttrsFilter ?? []
  );

  const hasReferral = results.length > 0 ? results[0].referrals : false;

  const handleKeyPress = (event) => {
    if (event.key === "Enter") {
      const params = new URLSearchParams(location.search);
      params.set("entry_name", entryFilter);
      params.set("referral_name", referralFilter);
      params.set(
        "attrinfo",
        JSON.stringify(
          Object.keys(attrsFilter).map((key) => ({
            name: key,
            keyword: attrsFilter[key],
          }))
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
    <StyledBox>
      <TableContainer component={Paper} sx={{ overflowX: "inherit" }}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: "primary.dark" }}>
              {/* FIXME avoid overlapping elements when scrolling */}
              <TableCell
                sx={{
                  color: "primary.contrastText",
                  minWidth: "300px",
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
          </TableHead>
          <TableBody>
            {results.map((result, index) => (
              <StyledTableRow key={index}>
                {/* FIXME avoid overlapping elements when scrolling */}
                <TableCell
                  sx={{
                    backgroundColor: "inherit",
                    minWidth: "300px",
                  }}
                >
                  <Box
                    component={Link}
                    to={entryDetailsPath(0, result.entry.id)}
                  >
                    {result.entry.name}
                  </Box>
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
                    <List>
                      {result.referrals.map((referral) => (
                        <ListItem>
                          <Box
                            key={referral.id}
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
            count={maxPage}
            page={page}
            onChange={(e, page) => handleChangePage(page)}
            color="primary"
          />
        </Stack>
      </Box>
    </StyledBox>
  );
};
