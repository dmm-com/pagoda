import { TableCell, TableCellProps } from "@mui/material";
import { styled } from "@mui/material/styles";
import { SxProps, Theme } from "@mui/system";
import { ComponentType } from "react";

type StyledTableCellProps = TableCellProps & {
  sx?: SxProps<Theme>;
};

export const AironeTableHeadCell: ComponentType<StyledTableCellProps> = styled(
  TableCell,
)<StyledTableCellProps>({
  color: "#FFFFFF",
}) as ComponentType<StyledTableCellProps>;
