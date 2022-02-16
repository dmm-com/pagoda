import {
  Table,
  TableContainer,
  TableHead,
  TableBody,
  TableCell,
  TableRow,
  Paper,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

import { AttributeValue } from "components/entry/AttributeValue";

interface Props {
  attributes: any;
}

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#607D8B0A",
  },
  "&:last-child td, &:last-child th": {
    border: 0,
  },
}));

export const EntryAttributes: FC<Props> = ({ attributes }) => {
  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead sx={{ backgroundColor: "primary.dark" }}>
          <TableRow>
            <TableCell sx={{ color: "primary.contrastText" }}>項目</TableCell>
            <TableCell sx={{ color: "primary.contrastText" }}>内容</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {Object.keys(attributes).map((attrname) => (
            <StyledTableRow key={attrname}>
              <TableCell sx={{ width: "400px" }}>{attrname}</TableCell>
              <TableCell sx={{ width: "750px", p: "0px" }}>
                <AttributeValue attrInfo={attributes[attrname]} />
              </TableCell>
            </StyledTableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
