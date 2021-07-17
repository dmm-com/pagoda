import React, { useReducer } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import Paper from "@material-ui/core/Paper";
import PropTypes from "prop-types";

export default function SearchResults({ results }) {
  const [entryFilter, entryFilterDispatcher] = useReducer((state, event) => {
    if (event.key === "Enter") {
      return event.target.value;
    }
    return state;
  }, "");
  const [attrsFilter, attrsFilterDispatcher] = useReducer(
    (state, { event, name }) => {
      if (event.key === "Enter") {
        return { ...state, [name]: event.target.value };
      }
      return state;
    },
    {}
  );

  const attrNames = results.length > 0 ? Object.keys(results[0].attrs) : [];

  const filtered = results
    .filter((r) => r.entry.name.includes(entryFilter))
    .filter((r) =>
      attrNames.every((name) => {
        const target = r.attrs[name].value || "";
        return target.includes(attrsFilter[name] || "");
      })
    );

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>
              <Typography>Name</Typography>
              <input
                text="text"
                placeholder="絞り込む"
                onKeyPress={entryFilterDispatcher}
              />
            </TableCell>
            {attrNames.map((attrName) => (
              <TableCell>
                <Typography>{attrName}</Typography>
                <input
                  text="text"
                  placeholder="絞り込む"
                  onKeyPress={(e) =>
                    attrsFilterDispatcher({ event: e, name: attrName })
                  }
                />
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {filtered.map((result) => (
            <TableRow>
              <TableCell>
                <Typography>{result.entry.name}</Typography>
              </TableCell>
              {attrNames.map((attrName) => (
                <TableCell>
                  {result.attrs[attrName] && (
                    <Typography>{result.attrs[attrName].value}</Typography>
                  )}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

SearchResults.propTypes = {
  results: PropTypes.array.isRequired,
};
