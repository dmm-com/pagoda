import { TableCell, TableRow } from "@mui/material";
import { styled } from "@mui/material/styles";

export const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

export const HeaderTableCell = styled(TableCell)(({}) => ({
  color: "#FFFFFF",
  boxSizing: "border-box",
}));

export const StyledTableRow = styled(TableRow)(({}) => ({
  "& td": {
    padding: "8px",
  },
}));
