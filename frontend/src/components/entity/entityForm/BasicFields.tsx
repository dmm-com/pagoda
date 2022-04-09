import {
  Box,
  Checkbox,
  Input,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import React, { FC } from "react";

interface Props {
  name: string;
  note: string;
  isTopLevel: boolean;
  setName: (name: string) => void;
  setNote: (note: string) => void;
  setIsTopLevel: (isTopLevel: boolean) => void;
}

export const BasicFields: FC<Props> = ({
  name,
  note,
  isTopLevel,
  setName,
  setNote,
  setIsTopLevel,
}) => {
  return (
    <Box>
      <Box my="32px">
        <Typography variant="h4" align="center">
          基本情報
        </Typography>
      </Box>

      <Table className="table table-bordered">
        <TableHead>
          <TableRow sx={{ backgroundColor: "#455A64" }}>
            <TableCell sx={{ color: "#FFFFFF" }}>項目</TableCell>
            <TableCell sx={{ color: "#FFFFFF" }}>内容</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>エンティティ名</TableCell>
            <TableCell>
              <Input
                type="text"
                value={name}
                placeholder="エンティティ名"
                sx={{ width: "100%" }}
                onChange={(e) => setName(e.target.value)}
              />
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>備考</TableCell>
            <TableCell>
              <Input
                type="text"
                value={note}
                placeholder="備考"
                sx={{ width: "100%" }}
                onChange={(e) => setNote(e.target.value)}
              />
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>サイドバーに表示</TableCell>
            <TableCell>
              <Checkbox
                checked={isTopLevel}
                onChange={(e) => setIsTopLevel(e.target.checked)}
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Box>
  );
};
