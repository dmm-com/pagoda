import {
  AdvancedSearchResult,
  EntryAttributeTypeTypeEnum,
  EntryAttributeValue,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import CloseIcon from "@mui/icons-material/Close";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { FC, useMemo } from "react";

function attrValueToKey(
  value: EntryAttributeValue,
  attrType: number,
): string {
  switch (attrType) {
    case EntryAttributeTypeTypeEnum.OBJECT:
      return value.asObject?.name ?? "";
    case EntryAttributeTypeTypeEnum.STRING:
    case EntryAttributeTypeTypeEnum.TEXT:
    case EntryAttributeTypeTypeEnum.DATE:
    case EntryAttributeTypeTypeEnum.DATETIME:
      return value.asString ?? "";
    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return value.asBoolean !== undefined ? String(value.asBoolean) : "";
    case EntryAttributeTypeTypeEnum.NUMBER:
      return value.asNumber != null ? String(value.asNumber) : "";
    case EntryAttributeTypeTypeEnum.NAMED_OBJECT: {
      const no = value.asNamedObject;
      if (!no) return "";
      const objName = no.object?.name ?? "";
      return no.name ? `${no.name} / ${objName}` : objName;
    }
    case EntryAttributeTypeTypeEnum.GROUP:
      return value.asGroup?.name ?? "";
    case EntryAttributeTypeTypeEnum.ROLE:
      return value.asRole?.name ?? "";
    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
      return value.asArrayObject?.map((o) => o.name).join(", ") ?? "";
    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      return value.asArrayString?.join(", ") ?? "";
    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
      return (
        value.asArrayNamedObject
          ?.map((o) =>
            o.name
              ? `${o.name} / ${o.object?.name ?? ""}`
              : (o.object?.name ?? ""),
          )
          .join(", ") ?? ""
      );
    case EntryAttributeTypeTypeEnum.ARRAY_GROUP:
      return value.asArrayGroup?.map((g) => g.name).join(", ") ?? "";
    case EntryAttributeTypeTypeEnum.ARRAY_ROLE:
      return value.asArrayRole?.map((r) => r.name).join(", ") ?? "";
    case EntryAttributeTypeTypeEnum.ARRAY_NUMBER:
      return (
        value.asArrayNumber
          ?.map((n) => (n != null ? String(n) : ""))
          .join(", ") ?? ""
      );
    default:
      return "";
  }
}

interface Props {
  open: boolean;
  onClose: () => void;
  attrname: string;
  results: AdvancedSearchResult;
  attrType: number;
}

export const AttrStatsModal: FC<Props> = ({
  open,
  onClose,
  attrname,
  results,
  attrType,
}) => {
  const stats = useMemo(() => {
    const counts = new Map<string, number>();
    for (const row of results.values) {
      const attr = row.attrs[attrname];
      if (!attr || !attr.isReadable) continue;
      const key = attrValueToKey(attr.value, attrType) || "(空白)";
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([value, count]) => ({ value, count }))
      .sort((a, b) => b.count - a.count);
  }, [results.values, attrname, attrType]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        「{attrname}」の集計
        <IconButton
          onClick={onClose}
          sx={{ position: "absolute", right: 8, top: 8 }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>値</TableCell>
                <TableCell align="right">件数</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {stats.map(({ value, count }) => (
                <TableRow key={value}>
                  <TableCell>{value}</TableCell>
                  <TableCell align="right">{count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </DialogContent>
    </Dialog>
  );
};
