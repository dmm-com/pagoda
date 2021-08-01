import React from "react";
import { Table, TableCell, TableRow } from "@material-ui/core";
import PropTypes from "prop-types";

export default function EntryAttributes({ attributes }) {
  return (
    <Table>
      {attributes.map((attr) => (
        <TableRow>
          <TableCell>{attr.name}</TableCell>
          <TableCell>{attr.value}</TableCell>
        </TableRow>
      ))}
    </Table>
  );
}

EntryAttributes.propTypes = {
  attributes: PropTypes.array.isRequired,
};
