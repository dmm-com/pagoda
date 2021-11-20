import {
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TablePagination,
} from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import * as React from "react";
import { FC, ReactElement, useState } from "react";

interface Props {
  rows: any[];
  tableHeadRow: ReactElement;
  tableBodyRowGenerator: (row: any) => ReactElement;
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
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(rowsPerPageOptions[0] ?? 0);

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
              .map((row) => tableBodyRowGenerator(row))}
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
