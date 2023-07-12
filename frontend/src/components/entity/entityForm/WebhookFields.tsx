import AddIcon from "@mui/icons-material/Add";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import ModeEditOutlineOutlinedIcon from "@mui/icons-material/ModeEditOutlineOutlined";
import {
  Box,
  Checkbox,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller, useFieldArray } from "react-hook-form";

import { Schema } from "./EntityFormSchema";
import { WebhookHeadersModal } from "./WebhookHeadersModal";

const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({}) => ({
  color: "#FFFFFF",
  boxSizing: "border-box",
}));

const StyledTableRow = styled(TableRow)(({}) => ({
  "& td": {
    padding: "8px",
    verticalAlign: "top",
  },
}));

interface Props {
  control: Control<Schema>;
}

export const WebhookFields: FC<Props> = ({ control }) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: "webhooks",
    keyName: "key", // NOTE: webhook has 'id' field conflicts default key name
  });

  const handleAppendWebhook = (nextTo: number) => {
    insert(nextTo, {
      id: undefined,
      url: "",
      label: "",
      isEnabled: false,
      isVerified: undefined,
      headers: [],
    });
  };

  const handleDeleteWebhook = (index: number) => {
    remove(index);
  };

  const [openModalIndex, setOpenModalIndex] = React.useState(-1);
  const handleOpenModal = (webhookIndex: number) => {
    setOpenModalIndex(webhookIndex);
  };
  const handleCloseModal = () => setOpenModalIndex(-1);

  return (
    <>
      <Typography variant="h4" align="center" my="16px">
        Webhook
      </Typography>

      <Table id="table_webhook_list">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell width="50px" />
            <HeaderTableCell width="400px">URL</HeaderTableCell>
            <HeaderTableCell width="350px">ラベル</HeaderTableCell>
            <HeaderTableCell width="100px">Header</HeaderTableCell>
            <HeaderTableCell width="100px">有効</HeaderTableCell>
            <HeaderTableCell width="100px">削除</HeaderTableCell>
            <HeaderTableCell width="100px">追加</HeaderTableCell>
          </HeaderTableRow>
        </TableHead>
        <TableBody>
          {fields.map((field, index) => (
            <StyledTableRow key={field.id}>
              <TableCell>
                <Box my="6px">
                  <Controller
                    name={`webhooks.${index}.isVerified`}
                    control={control}
                    render={({ field }) => {
                      switch (field.value) {
                        case undefined:
                          return <></>;
                        case true:
                          return <CheckCircleOutlineIcon color="success" />;
                        case false:
                          return <ErrorOutlineIcon color="error" />;
                      }
                    }}
                  />
                </Box>
              </TableCell>
              <TableCell>
                <Controller
                  name={`webhooks.${index}.url`}
                  control={control}
                  defaultValue=""
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      id="webhook-url"
                      placeholder="URL"
                      error={error != null}
                      helperText={error?.message}
                      size="small"
                      fullWidth
                    />
                  )}
                />
              </TableCell>
              <TableCell>
                <Controller
                  name={`webhooks.${index}.label`}
                  control={control}
                  defaultValue=""
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      placeholder="ラベル"
                      error={error != null}
                      helperText={error?.message}
                      size="small"
                      fullWidth
                    />
                  )}
                />
              </TableCell>
              <TableCell>
                <IconButton onClick={() => handleOpenModal(index)}>
                  <ModeEditOutlineOutlinedIcon />
                </IconButton>
              </TableCell>
              <TableCell>
                <Controller
                  name={`webhooks.${index}.isEnabled`}
                  control={control}
                  defaultValue={false}
                  render={({ field }) => (
                    <Checkbox
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                    />
                  )}
                />
              </TableCell>
              <TableCell>
                <IconButton onClick={() => handleDeleteWebhook(index)}>
                  <DeleteOutlineIcon />
                </IconButton>
              </TableCell>
              <TableCell>
                <IconButton onClick={() => handleAppendWebhook(index + 1)}>
                  <AddIcon />
                </IconButton>
              </TableCell>
            </StyledTableRow>
          ))}
          {fields.length === 0 && (
            <StyledTableRow>
              <TableCell />
              <TableCell />
              <TableCell />
              <TableCell />
              <TableCell />
              <TableCell />
              <TableCell>
                <IconButton onClick={() => handleAppendWebhook(0)}>
                  <AddIcon />
                </IconButton>
              </TableCell>
            </StyledTableRow>
          )}
        </TableBody>
      </Table>
      {openModalIndex >= 0 && (
        <WebhookHeadersModal
          webhookIndex={openModalIndex}
          handleCloseModal={handleCloseModal}
          control={control}
        />
      )}
    </>
  );
};
