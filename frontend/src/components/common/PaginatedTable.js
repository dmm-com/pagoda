import {
  Paper,
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TablePagination,
} from "@mui/material";
import PropTypes from "prop-types";
import React, { useState } from "react";

/**
 * Paginate table shows given rows
 *
 */
export function PaginatedTable({
  rows,
  tableHeadRow,
  tableBodyRowGenerator,
  rowsPerPageOptions,
}) {
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
}

PaginatedTable.propTypes = {
  rows: PropTypes.array.isRequired,
  tableHeadRow: PropTypes.object.isRequired,
  tableBodyRowGenerator: PropTypes.func.isRequired,
  rowsPerPageOptions: PropTypes.arrayOf(PropTypes.number).isRequired,
};
