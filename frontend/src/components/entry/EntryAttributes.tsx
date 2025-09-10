import { EntryAttributeType } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC } from "react";

import { AttributeValue } from "components/entry/AttributeValue";

interface Props {
  attributes: Array<EntryAttributeType>;
}

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#607D8B0A",
  },
  "&:last-child td, &:last-child th": {
    border: 0,
  },
  "& td": {
    padding: "8px 16px",
  },
}));

const HeaderTableCell = styled(TableCell)(({ theme }) => ({
  color: theme.palette.primary.contrastText,
}));

const AttrNameTableCell = styled(TableCell)(() => ({
  width: "200px",
  wordBreak: "break-word",
}));

const AttrValueTableCell = styled(TableCell)(() => ({
  width: "950px",
  wordBreak: "break-word",
}));

export const EntryAttributes: FC<Props> = ({ attributes }) => {
  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead sx={{ backgroundColor: "primary.dark" }}>
          <TableRow>
            <HeaderTableCell>項目</HeaderTableCell>
            <HeaderTableCell>内容</HeaderTableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {attributes.map((attr) => (
            <StyledTableRow key={attr.schema.name}>
              <AttrNameTableCell>{attr.schema.name}</AttrNameTableCell>
              <AttrValueTableCell>
                {attr.isReadable ? (
                  <AttributeValue
                    attrInfo={{ type: attr.type, value: attr.value }}
                  />
                ) : (
                  <Typography>Permission denied.</Typography>
                )}
              </AttrValueTableCell>
            </StyledTableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
