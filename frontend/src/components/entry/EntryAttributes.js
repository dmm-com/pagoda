import { Table, TableBody, TableCell, TableRow } from "@material-ui/core";
import PropTypes from "prop-types";
import React from "react";

import { groupsPath, showEntryPath } from "../../Routes";
import { DjangoContext } from "../../utils/DjangoContext";

import { AttributeValue } from "./AttributeValue";

export default function EntryAttributes({ attributes }) {
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
