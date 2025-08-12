import {
  TableCell,
  TableRow,
  TableCellProps,
  TableRowProps,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { SxProps, Theme } from "@mui/system";
import React from "react";

type StyledTableRowProps = TableRowProps & {
  sx?: SxProps<Theme>;
};

type StyledTableCellProps = TableCellProps & {
  sx?: SxProps<Theme>;
};

export const HeaderTableRow: React.ComponentType<StyledTableRowProps> = styled(
  TableRow,
)<StyledTableRowProps>({
  backgroundColor: "#455A64",
}) as React.ComponentType<StyledTableRowProps>;

export const HeaderTableCell: React.ComponentType<StyledTableCellProps> =
  styled(TableCell)<StyledTableCellProps>({
    color: "#FFFFFF",
    boxSizing: "border-box",
  }) as React.ComponentType<StyledTableCellProps>;

export const StyledTableRow: React.ComponentType<StyledTableRowProps> = styled(
  TableRow,
)<StyledTableRowProps>({
  "& td": {
    padding: "8px",
  },
}) as React.ComponentType<StyledTableRowProps>;
