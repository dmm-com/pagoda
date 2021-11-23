import {
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TablePagination,
} from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import React, { FC, ReactElement, useState } from "react";

interface Props {
  rows: any[];
  tableHeadRow: ReactElement;
  tableBodyRowGenerator: (row: any, index: number) => ReactElement;
  rowsPerPageOptions: number[];
}

/**
 * Paginate table shows given rows
 *
 */
export const PaginatedTable: FC<Props> = ({
  rows,
  tableHeadRow,
  tableBodyRowGenerator,
  rowsPerPageOptions,
}) => {
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
      <TableContainer component={Paper}>
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
