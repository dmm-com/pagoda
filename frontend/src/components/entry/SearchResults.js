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
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import PropTypes from "prop-types";
import React, { useReducer } from "react";
import { useHistory, useLocation } from "react-router-dom";
import { DjangoContext } from "../../utils/DjangoContext";


function ElemString({attrValue}) {
  return (<div>{attrValue}</div>);
}

function ElemObject({attrValue}) {
  console.log(attrValue);
  console.log(`[onix-test/ElemObject(50)] attrValue: ${attrValue}`);
  return <a href={`/entry/show/${attrValue.id}`}>{attrValue.name}</a>
}

function ElemNamedObject({attrValue}) {
  const key = Object.keys(attrValue)[0];
  return <div><div>{key}</div>: <a href={`/entry/show/${attrValue[key].id}`}>{attrValue[key].name}</a></div>;
}


export function convertAttributeValue(attrName, attrInfo) {
  /* Convert attrValue according to type of attrValue */
  console.log(`===== ${attrName} (${attrInfo.type}) =====`);
  console.log(attrInfo.value);

  const djangoContext = DjangoContext.getInstance();
  let convertedValue = '';

  switch(attrInfo.type) {
    case djangoContext.attrTypeValue.object:
      //return <ElemObject attrValue={attrInfo.value} />;
      break;

    case djangoContext.attrTypeValue.string:
      console.log(`[onix-test(40)] attrType: ${attrInfo.type}`);
      return <ElemString attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.named_object:
      return <ElemNamedObject attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.array_object:
      return (<List>
        {attrInfo.value.map((info, n) => {
          return <ListItem key={n}>
            <ElemObject attrValue={info} />
          </ListItem>
        })}
      </List>)

    case djangoContext.attrTypeValue.array_string:
      return (<List>
        {attrInfo.value.map((info, n) => {
          return <ListItem key={n}>
            <ElemString attrValue={info} />
          </ListItem>
        })}
      </List>)

    case djangoContext.attrTypeValue.array_named_object:
      return (<List>
        {attrInfo.value.map((info, n) => {
          return <ListItem key={n}>
            <ElemNamedObject attrValue={info} />
          </ListItem>
        })}
      </List>)

    case djangoContext.attrTypeValue.array_group:
      // XXX
      break;

    case djangoContext.attrTypeValue.text:
      // XXX
      break;
    case djangoContext.attrTypeValue.boolean:
      // XXX
      break;
    case djangoContext.attrTypeValue.group:
      // XXX
      break;
    case djangoContext.attrTypeValue.date:
      // XXX
      break;
  }

  // XXX: DEBUG
  return 'hoge';
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
                        <>
                          { convertAttributeValue(attrName, result.attrs[attrName]) }
                          {/* result.attrs[attrName].value.toString() */}
                        </>
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
