import AddIcon from "@mui/icons-material/Add";
import { Button, TableBody, TableCell, TableRow } from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, useCallback } from "react";

/**
 * Focus target selector used after a row is inserted. Autocomplete inputs are
 * rendered as buttons with `role="combobox"`, so they are included here.
 */
const FIRST_CONTROL_SELECTOR =
  'input:not([type="hidden"]), textarea, [role="combobox"]';

/**
 * Shared row-insertion affordances.
 *
 * The previous UI attached a plain "+" icon to every row. That control lived in
 * the middle of the row while its effect happened *between* rows, so the
 * insertion point had to be guessed, and the icon moved down every time a row
 * was added. These components split the two intents:
 *
 * - `AddRowButton` / `AppendRow`: always-visible append control at the end of
 *   the list (Notion/Airtable "new row" behaviour). Covers the common case.
 * - `InsertBand` / `InsertBandRow`: a divider-shaped control rendered exactly on
 *   the boundary where the new row appears, so the control and the result share
 *   one position.
 */

/**
 * Moves focus into the row that was just inserted. Rows opt in by carrying
 * `data-list-id` and `data-row-index`.
 */
export const useInsertedRowFocus = (listId: string) =>
  useCallback(
    (index: number) => {
      // The new row is not in the DOM until React commits, and its inputs are
      // not registered with react-hook-form until the next paint.
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          const row = document.querySelector<HTMLElement>(
            `[data-list-id="${listId}"][data-row-index="${index}"]`,
          );
          if (row == null) {
            return;
          }
          // jsdom (unit tests) does not implement scrollIntoView.
          row.scrollIntoView?.({ block: "nearest" });
          const control = row.querySelector<HTMLElement>(
            FIRST_CONTROL_SELECTOR,
          );
          (control ?? row).focus();
        });
      });
    },
    [listId],
  );

const AppendButton = styled(Button, {
  shouldForwardProp: (prop) => prop !== "rowHeight",
})<{ rowHeight: number }>(({ theme, rowHeight }) => ({
  justifyContent: "flex-start",
  width: "100%",
  minHeight: rowHeight,
  paddingLeft: 0,
  color: theme.palette.text.secondary,
  fontWeight: 400,
  fontSize: "0.875rem",
  borderRadius: 0,
  // Reads as the next row: the whole row highlights on hover instead of the
  // control looking like a standalone button.
  "&:hover": {
    color: theme.palette.primary.main,
    backgroundColor: theme.palette.action.hover,
  },
}));

interface AddRowButtonProps {
  onAdd: () => void;
  label?: string;
  ariaLabel?: string;
  testId?: string;
  disabled?: boolean;
  /** Height of the row this control represents. */
  rowHeight?: number;
}

/**
 * Append control that always adds a row at the very end of the list.
 * The label is intentional: an unlabelled icon does not say where the row goes.
 */
export const AddRowButton: FC<AddRowButtonProps> = ({
  onAdd,
  label = "追加",
  ariaLabel,
  testId = "append-row",
  disabled = false,
  rowHeight = 40,
}) => (
  <AppendButton
    type="button"
    data-testid={testId}
    aria-label={ariaLabel}
    disabled={disabled}
    rowHeight={rowHeight}
    onClick={onAdd}
    startIcon={<AddIcon fontSize="small" />}
  >
    {label}
  </AppendButton>
);

const BandButton = styled("button", {
  shouldForwardProp: (prop) => prop !== "dense",
})<{ dense?: boolean }>(({ theme, dense }) => ({
  all: "unset",
  boxSizing: "border-box",
  position: "relative",
  display: "flex",
  alignItems: "center",
  justifyContent: "flex-start",
  width: "100%",
  height: dense === true ? 10 : 12,
  cursor: "pointer",
  borderRadius: 0,
  paddingLeft: theme.spacing(1),
  // Jira-style: the gap is invisible until the pointer or keyboard reaches it,
  // so a long list is not covered in rules, but every gap stays reachable.
  "&::before": {
    content: '""',
    position: "absolute",
    left: 0,
    right: 0,
    top: "50%",
    borderTopWidth: 2,
    borderTopStyle: "solid",
    borderTopColor: theme.palette.primary.main,
    opacity: 0,
    transition: "opacity 100ms ease",
  },
  "&:hover, &:focus-visible": {
    "&::before": {
      opacity: 1,
    },
  },
  "&:focus-visible": {
    outline: `2px solid ${theme.palette.primary.main}`,
    outlineOffset: -2,
  },
}));

const BandChip = styled("span")<{ dense?: boolean }>(({ theme, dense }) => ({
  position: "relative",
  zIndex: 1,
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  width: dense === true ? 16 : 20,
  height: dense === true ? 16 : 20,
  borderRadius: "50%",
  backgroundColor: theme.palette.background.paper,
  border: `1px solid ${theme.palette.divider}`,
  color: theme.palette.primary.main,
  borderColor: theme.palette.primary.main,
  opacity: 0,
  transition: "opacity 100ms ease",
  "button:hover &, button:focus-visible &": {
    opacity: 1,
  },
}));

interface InsertBandProps {
  /**
   * Insertion boundary. `insert(index, row)` makes the new row land at `index`,
   * i.e. this band sits directly above that position.
   */
  index: number;
  ariaLabel: string;
  onInsert: (index: number) => void;
  testId?: string;
  dense?: boolean;
}

/** The bare control, for lists whose rows are not table rows. */
export const InsertBand: FC<InsertBandProps> = ({
  index,
  ariaLabel,
  onInsert,
  testId = `insert-band-${index}`,
  dense = false,
}) => (
  <BandButton
    type="button"
    data-testid={testId}
    aria-label={ariaLabel}
    dense={dense}
    onClick={() => onInsert(index)}
  >
    <BandChip dense={dense} aria-hidden="true">
      <AddIcon style={{ fontSize: dense === true ? 12 : 14 }} />
    </BandChip>
  </BandButton>
);

interface InsertBandRowProps extends InsertBandProps {
  colSpan: number;
}

/** Table variant. Keeps the band out of the column grid. */
export const InsertBandRow: FC<InsertBandRowProps> = ({
  colSpan,
  ...props
}) => (
  <TableRow data-insert-band="true">
    <TableCell colSpan={colSpan} sx={{ p: 0, border: 0, height: 0 }}>
      <InsertBand {...props} />
    </TableCell>
  </TableRow>
);

interface AppendRowProps {
  onAdd: () => void;
  colSpan: number;
  label?: string;
  ariaLabel?: string;
  testId?: string;
}

/** Table variant of `AddRowButton`, rendered as the last table row. */
export const AppendRow: FC<AppendRowProps> = ({
  onAdd,
  colSpan,
  label,
  ariaLabel,
  testId = "append-row",
}) => (
  <TableRow
    data-append-row="true"
    sx={{
      "&:hover": { backgroundColor: "action.hover" },
      "& td": { padding: 0 },
    }}
  >
    <TableCell colSpan={colSpan}>
      <AddRowButton
        onAdd={onAdd}
        label={label}
        ariaLabel={ariaLabel}
        testId={testId}
        rowHeight={52}
      />
    </TableCell>
  </TableRow>
);

/**
 * Table body with striping driven by an explicit attribute.
 *
 * `tr:nth-of-type()` cannot be used any more: insertion bands are table rows as
 * well, and they would consume the odd/even sequence.
 */
export const RepeatableTableBody = styled(TableBody)({
  "& tr[data-stripe='odd']": {
    backgroundColor: "white",
  },
  "& tr[data-stripe='even']": {
    backgroundColor: "#607D8B0A",
  },
  "& td": {
    padding: "8px",
  },
});

export const stripeFor = (index: number) => (index % 2 === 0 ? "odd" : "even");
