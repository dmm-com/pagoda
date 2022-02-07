/**
 * @jest-environment jsdom
 */
import { TableCell, TableRow } from "@mui/material";
import { render } from "@testing-library/react";
import React from "react";

import { PaginatedTable } from "components/common/PaginatedTable";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <PaginatedTable
        rows={[1, 2, 3, 4, 5]}
        tableHeadRow={
          <TableRow>
            <TableCell>
              <p>test cell</p>
            </TableCell>
          </TableRow>
        }
        tableBodyRowGenerator={(row) => (
          <TableRow key={row}>
            <TableCell>
              <p>{row}</p>
            </TableCell>
          </TableRow>
        )}
        rowsPerPageOptions={[1, 5, 10]}
      />,
      { wrapper: TestWrapper }
    )
  ).not.toThrow();
});
