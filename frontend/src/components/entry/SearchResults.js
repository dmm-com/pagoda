import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
} from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";
import PropTypes from "prop-types";
import React, { useReducer } from "react";
import { useHistory, useLocation } from "react-router-dom";
import { DjangoContext } from "../utils/DjangoContext";

function convertAttributeValue(attrName, attrInfo) {
  /* Convert attrValue according to type of attrValue */
  console.log(`===== ${attrName} (${attrInfo.type}) =====`);
  console.log(attrInfo.value);
  let convertedValue = '';

  switch(attrInfo.type) {
    case DjangoContext.attrTypeValue.object:
      // XXX
    case DjangoContext.attrTypeValue.string:
      // XXX
    case DjangoContext.attrTypeValue.named_object:
      // XXX
    case DjangoContext.attrTypeValue.array_object:
      // XXX
    case DjangoContext.attrTypeValue.array_string:
      // XXX
    case DjangoContext.attrTypeValue.array_named_object:
      // XXX
    case DjangoContext.attrTypeValue.array_group:
      // XXX
    case DjangoContext.attrTypeValue.text:
      // XXX
    case DjangoContext.attrTypeValue.boolean:
      // XXX
    case DjangoContext.attrTypeValue.group:
      // XXX
    case DjangoContext.attrTypeValue.date:
      // XXX
  }

  // XXX: DEBUG
  return convertedValue;
}


export function SearchResults({
  results,
  defaultEntryFilter = "",
  defaultAttrsFilter = {},
}) {
  const location = useLocation();
  const history = useHistory();

  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(100);

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

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  return (
    <Paper>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
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
          </TableHead>
          <TableBody>
            {results
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((result, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Typography>{result.entry.name}</Typography>
                  </TableCell>
                  {attrNames.map((attrName) => (
                    <TableCell key={attrName}>
                      {/* TODO switch how to render values based on the type */}
                      {result.attrs[attrName] && (
                        <Typography>
                          { convertAttributeValue(attrName, result.attrs[attrName]) }
                          {/* result.attrs[attrName].value.toString() */}
                        </Typography>
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[100, 250, 1000]}
        component="div"
        count={results.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handlePageChange}
        onRowsPerPageChange={handleRowsPerPageChange}
      />
    </Paper>
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
