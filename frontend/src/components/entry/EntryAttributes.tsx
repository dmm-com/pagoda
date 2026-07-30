import {
  EntryAttributeType,
  TriggerParent,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import {
  Box,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, useMemo } from "react";

import { AttributeValue } from "components/entry/AttributeValue";
import { triggersPath } from "routes/Routes";

interface Props {
  attributes: Array<EntryAttributeType>;
  triggers?: TriggerParent[];
  /** Description of each attribute (EntityAttr.note), keyed by EntityAttr id */
  attrNotes?: Record<number, string>;
}

const StyledTableRow = styled(TableRow)<{ highlighted?: boolean }>(
  ({ highlighted }) => ({
    "&:nth-of-type(odd)": {
      backgroundColor: highlighted ? "#BBDEFB" : "#607D8B0A",
    },
    "&:nth-of-type(even)": {
      backgroundColor: highlighted ? "#BBDEFB" : undefined,
    },
    "&:last-child td, &:last-child th": {
      border: 0,
    },
    "& td": {
      padding: "8px 16px",
    },
  }),
);

const HeaderTableCell = styled(TableCell)(({ theme }) => ({
  color: theme.palette.primary.contrastText,
}));

const AttrNameTableCell = styled(TableCell)(() => ({
  width: "30%",
  minWidth: "180px",
  maxWidth: "320px",
  wordBreak: "break-word",
}));

const AttrValueTableCell = styled(TableCell)(() => ({
  width: "70%",
  wordBreak: "break-word",
}));

const AttrNameBox = styled(Box)(() => ({
  display: "flex",
  alignItems: "center",
  gap: "4px",
}));

const AttrNoteIcon = styled(HelpOutlineIcon)(({ theme }) => ({
  fontSize: "16px",
  color: theme.palette.text.disabled,
  cursor: "help",
  "&:hover": {
    color: theme.palette.text.secondary,
  },
}));

export const EntryAttributes: FC<Props> = ({
  attributes,
  triggers,
  attrNotes = {},
}) => {
  const triggeredAttrIds = useMemo(
    () =>
      new Set(triggers?.flatMap((t) => t.actions.map((a) => a.attr.id)) ?? []),
    [triggers],
  );

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead sx={{ backgroundColor: "primary.dark" }}>
          <TableRow>
            <HeaderTableCell>項目</HeaderTableCell>
            <HeaderTableCell>内容</HeaderTableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {attributes.map((attr) => (
            <StyledTableRow
              key={attr.schema.name}
              highlighted={triggeredAttrIds.has(attr.schema.id)}
            >
              <AttrNameTableCell>
                <AttrNameBox>
                  {triggeredAttrIds.has(attr.schema.id) ? (
                    <Tooltip
                      title="この属性には Trigger が設定されています"
                      placement="top"
                    >
                      <Link href={triggersPath()}>{attr.schema.name}</Link>
                    </Tooltip>
                  ) : (
                    attr.schema.name
                  )}
                  {attrNotes[attr.schema.id] && (
                    <Tooltip
                      title={attrNotes[attr.schema.id]}
                      placement="top"
                      arrow
                      enterTouchDelay={0}
                    >
                      <AttrNoteIcon aria-label={`${attr.schema.name}の説明`} />
                    </Tooltip>
                  )}
                </AttrNameBox>
              </AttrNameTableCell>
              <AttrValueTableCell>
                {attr.isReadable ? (
                  <AttributeValue
                    attrInfo={{ type: attr.type, value: attr.value }}
                  />
                ) : (
                  <Typography>Permission denied.</Typography>
                )}
              </AttrValueTableCell>
            </StyledTableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
