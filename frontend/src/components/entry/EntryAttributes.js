import { Table, TableBody, TableCell, TableRow } from "@material-ui/core";
import PropTypes from "prop-types";
import React from "react";


function convertAttributeValue(attrName, attrInfo) {
  // ...
  //

  return (<>..results </>);
}

export default function EntryAttributes({ attributes }) {
  return (
    <Table>
      <TableBody>
        {attributes.map((attr) => (
          <TableRow key={attr.name}>
            <TableCell>{attr.name}</TableCell>
            <TableCell>
              {convertAttributeValue(attr.name, attr.value)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

EntryAttributes.propTypes = {
  attributes: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
    })
  ).isRequired,
};
