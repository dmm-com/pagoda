import { TableCell, TableRow } from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import PropTypes from "prop-types";
import React, { useReducer } from "react";
import { useHistory, useLocation } from "react-router-dom";

import { PaginatedTable } from "../common/PaginatedTable.tsx";

import { AttributeValue } from "./AttributeValue";

export function SearchResults({
  results,
  defaultEntryFilter = "",
  defaultAttrsFilter = {},
}) {
  const location = useLocation();
  const history = useHistory();

  const [entryFilter, entryFilterDispatcher] = useReducer((_, event) => {
    return event.target.value;
  }, defaultEntryFilter);
  const [attrsFilter, attrsFilterDispatcher] = useReducer(
    (state, { event, name }) => {
      return { ...state, [name]: event.target.value };
    },
    defaultAttrsFilter
  );

  const attrNames = results.length > 0 ? Object.keys(results[0].attrs) : [];

  const handleKeyPress = (event) => {
    if (event.key === "Enter") {
      const params = new URLSearchParams(location.search);
      params.set("entry_name", entryFilter);
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
        <TableRow>
          <TableCell>
            <Typography>Name</Typography>
            <input
              text="text"
              placeholder="絞り込む"
              defaultValue={defaultEntryFilter}
              onChange={entryFilterDispatcher}
              onKeyPress={handleKeyPress}
            />
          </TableCell>
          {attrNames.map((attrName) => (
            <TableCell key={attrName}>
              <Typography>{attrName}</Typography>
              <input
                text="text"
                placeholder="絞り込む"
                defaultValue={defaultAttrsFilter[attrName] || ""}
                onChange={(e) =>
                  attrsFilterDispatcher({ event: e, name: attrName })
                }
                onKeyPress={handleKeyPress}
              />
            </TableCell>
          ))}
        </TableRow>
      }
      tableBodyRowGenerator={(result, index) => (
        <TableRow key={index}>
          <TableCell>
            <Typography>{result.entry.name}</Typography>
          </TableCell>
          {attrNames.map((attrName) => (
            <TableCell key={attrName}>
              {result.attrs[attrName] && (
                <AttributeValue
                  attrName={attrName}
                  attrInfo={result.attrs[attrName]}
                />
              )}
            </TableCell>
          ))}
        </TableRow>
      )}
      rowsPerPageOptions={[100, 250, 1000]}
    />
  );
}

SearchResults.propTypes = {
  results: PropTypes.arrayOf(
    PropTypes.shape({
      attrs: PropTypes.object.isRequired,
      entry: PropTypes.shape({
        name: PropTypes.string.isRequired,
      }).isRequired,
    })
  ).isRequired,
  defaultEntryFilter: PropTypes.string,
  defaultAttrsFilter: PropTypes.object,
};
