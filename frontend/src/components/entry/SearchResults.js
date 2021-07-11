import React from "react";
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

export default function SearchResults({ results }) {
  let attrNames = [];
  if (results.length > 0) {
    attrNames = Object.keys(results[0].attrs);
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>
              <Typography>Name</Typography>
            </TableCell>
            {attrNames.map((attrName) => (
              <TableCell>
                <Typography>{attrName}</Typography>
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {results.map((result) => (
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
