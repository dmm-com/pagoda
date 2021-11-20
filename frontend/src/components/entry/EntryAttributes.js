import { Table, TableBody, TableCell, TableRow } from "@material-ui/core";
import PropTypes from "prop-types";
import React from "react";

import { AttributeValue } from "./AttributeValue";

export function EntryAttributes({ attributes }) {
  return (
    <Table>
      <TableBody>
        {Object.keys(attributes).map((attrname) => (
          <TableRow key={attrname}>
            <TableCell>{attrname}</TableCell>
            <TableCell>
              <AttributeValue
                attrName={attrname}
                attrInfo={attributes[attrname]}
              />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

EntryAttributes.propTypes = {
  attributes: PropTypes.object.isRequired,
};
