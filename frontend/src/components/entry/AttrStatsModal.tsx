import {
  AdvancedSearchResultAttrInfo,
  EntryAttributeTypeTypeEnum,
  EntryAttributeValue,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import CloseIcon from "@mui/icons-material/Close";
import {
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { FC, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router";

import { aironeApiClient } from "repository/AironeApiClient";
import { extractAdvancedSearchParams } from "services/entry/AdvancedSearch";

const PAGE_SIZE = 100;

function attrValueToKey(value: EntryAttributeValue, attrType: number): string {
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
  attrType: number;
  totalCount: number;
}

export const AttrStatsModal: FC<Props> = ({
  open,
  onClose,
  attrname,
  attrType,
  totalCount,
}) => {
  const location = useLocation();
  const [counts, setCounts] = useState<Map<string, number>>(new Map());
  const [loadedCount, setLoadedCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!open) {
      setCounts(new Map());
      setLoadedCount(0);
      setIsLoading(false);
      return;
    }

    if (totalCount === 0) return;

    const params = new URLSearchParams(location.search);
    const {
      entityIds,
      attrInfo,
      joinAttrs,
      hasReferral,
      referralName,
      searchAllEntities,
      hintEntry,
      referralExcludeModelIds,
      referralIncludeModelIds,
    } = extractAdvancedSearchParams(params);

    const filteredAttrInfo: AdvancedSearchResultAttrInfo[] = attrInfo.filter(
      (attr) => attr.name === attrname,
    );

    setCounts(new Map());
    setLoadedCount(0);
    setIsLoading(true);

    let cancelled = false;
    const totalPages = Math.ceil(totalCount / PAGE_SIZE);

    (async () => {
      for (let page = 1; page <= totalPages; page++) {
        if (cancelled) break;

        const results = await aironeApiClient.advancedSearch(
          entityIds,
          filteredAttrInfo,
          joinAttrs,
          hasReferral,
          referralName,
          searchAllEntities,
          page,
          PAGE_SIZE,
          0,
          hintEntry,
          referralExcludeModelIds,
          referralIncludeModelIds,
        );

        if (cancelled) break;

        setCounts((prev) => {
          const next = new Map(prev);
          for (const row of results.values) {
            const attr = row.attrs[attrname];
            if (!attr || !attr.isReadable) continue;
            const key = attrValueToKey(attr.value, attrType) || "(空白)";
            next.set(key, (next.get(key) ?? 0) + 1);
          }
          return next;
        });
        setLoadedCount((prev) => prev + results.values.length);
      }

      if (!cancelled) setIsLoading(false);
    })().catch(() => {
      if (!cancelled) setIsLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [open, location.search, attrname, attrType, totalCount]);

  const stats = useMemo(
    () =>
      Array.from(counts.entries())
        .map(([value, count]) => ({ value, count }))
        .sort((a, b) => b.count - a.count),
    [counts],
  );

  const displayedCount = isLoading
    ? Math.min(loadedCount, totalCount)
    : totalCount;
  const progress =
    totalCount > 0
      ? Math.min(Math.round((displayedCount / totalCount) * 100), 100)
      : 0;

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
        <Box sx={{ mb: 1 }}>
          <Box
            sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}
          >
            <Typography variant="caption" color="text.secondary">
              {displayedCount} / {totalCount} 件
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {progress}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{ borderRadius: 1 }}
          />
        </Box>
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
