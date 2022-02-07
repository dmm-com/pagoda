import { Table, TableBody, TableCell, TableRow } from "@mui/material";
import React, { FC } from "react";

import { AttributeValue } from "components/entry/AttributeValue";

interface Props {
  attributes: any;
}

export const EntryAttributes: FC<Props> = ({ attributes }) => {
  return (
    <Table>
      <TableBody>
        {Object.keys(attributes).map((attrname) => (
          <TableRow key={attrname}>
            <TableCell>{attrname}</TableCell>
            <TableCell>
              <AttributeValue attrInfo={attributes[attrname]} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
