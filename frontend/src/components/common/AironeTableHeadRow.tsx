import { TableRow, TableRowProps } from "@mui/material";
import { styled } from "@mui/material/styles";
import { SxProps, Theme } from "@mui/system";

type StyledTableRowProps = TableRowProps & {
  sx?: SxProps<Theme>;
};

export const AironeTableHeadRow: React.ComponentType<StyledTableRowProps> =
  styled(TableRow)<StyledTableRowProps>({
    backgroundColor: "#455A64",
  }) as React.ComponentType<StyledTableRowProps>;
