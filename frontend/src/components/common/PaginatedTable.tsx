import {
  Paper,
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TablePagination,
} from "@mui/material";
import React, { ReactElement, useState } from "react";

interface Props<T> {
  rows: T[];
  tableHeadRow: ReactElement;
  tableBodyRowGenerator: (row: T, index: number) => ReactElement;
  rowsPerPageOptions: number[];
}

/**
 * Paginate table shows given rows
 *
 */
export const PaginatedTable = <T,>({
  rows,
  tableHeadRow,
  tableBodyRowGenerator,
  rowsPerPageOptions,
}: Props<T>) => {
  const [page, setPage] = useState<number>(0);
  const [rowsPerPage, setRowsPerPage] = useState<number>(
    rowsPerPageOptions[0] ?? 0
  );

  const handleRowsPerPageChange = (event) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  return (
    <Paper>
      <TableContainer component={Paper} sx={{ overflowX: "inherit" }}>
        <Table>
          <TableHead>{tableHeadRow}</TableHead>
          <TableBody>
            {rows
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((row, index) => tableBodyRowGenerator(row, index))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={rowsPerPageOptions}
        component="div"
        count={rows.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(_, page) => setPage(page)}
        onRowsPerPageChange={handleRowsPerPageChange}
      />
    </Paper>
  );
};
