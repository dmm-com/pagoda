import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import ModeEditOutlineOutlinedIcon from "@mui/icons-material/ModeEditOutlineOutlined";
import {
  Box,
  Checkbox,
  IconButton,
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
  entityInfo: {
    name: string;
    note: string;
    isTopLevel: boolean;
    webhooks: any;
    attributes: { [key: string]: any }[];
  };
  setEntityInfo: (entityInfo: {
    name: string;
    note: string;
    isTopLevel: boolean;
    webhooks: any;
    attributes: { [key: string]: any }[];
  }) => void;
}

export const WebhookFields: FC<Props> = ({ entityInfo, setEntityInfo }) => {
  const handleChangeWebhook = (
    webhookId: number,
    url: string,
    label: string,
    enabled: boolean,
    headers: any[]
  ) => {
    setEntityInfo({
      ...entityInfo,
      webhooks: [], // TODO update webhooks
    });
  };

  return (
    <Box>
      <Box my="32px">
        <Typography variant="h4" align="center">
          Webhook
        </Typography>
      </Box>

      <Table className="table table-bordered">
        <TableHead>
          <TableRow sx={{ backgroundColor: "#455A64" }}>
            <TableCell sx={{ color: "#FFFFFF" }}>URL</TableCell>
            <TableCell sx={{ color: "#FFFFFF" }}>オプション</TableCell>
            <TableCell />
            <TableCell sx={{ color: "#FFFFFF" }}>URL有効化</TableCell>
            <TableCell sx={{ color: "#FFFFFF" }}>削除</TableCell>
            <TableCell sx={{ color: "#FFFFFF" }}>追加</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {entityInfo.webhooks.map((webhook) => (
            <TableRow key={webhook.id}>
              {/* TODO show isAvailable ??? */}
              {/* TODO update webhook */}
              <TableCell>
                <Input
                  type="text"
                  value={webhook.url}
                  placeholder="URL"
                  sx={{ width: "100%" }}
                />
              </TableCell>
              <TableCell>
                <Input
                  type="text"
                  value={webhook.label}
                  placeholder="Label"
                  sx={{ width: "100%" }}
                />
              </TableCell>
              <TableCell>
                <IconButton>
                  <ModeEditOutlineOutlinedIcon />
                </IconButton>
              </TableCell>
              <TableCell>
                <Checkbox checked={webhook.enabled} />
              </TableCell>
              <TableCell>
                <IconButton>
                  <DeleteOutlineIcon />
                </IconButton>
              </TableCell>
              <TableCell>
                <IconButton>
                  <AddIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  );
};
