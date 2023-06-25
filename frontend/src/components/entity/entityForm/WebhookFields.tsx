import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
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
import React, { FC, Fragment } from "react";
import { Control, Controller, useFieldArray } from "react-hook-form";

import { Schema } from "./EntityFormSchema";
import { WebhookHeadersModal } from "./WebhookHeadersModal";

const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({}) => ({
  color: "#FFFFFF",
}));

interface Props {
  control: Control<Schema>;
}

export const WebhookFields: FC<Props> = ({ control }) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: "webhooks",
  });

  const handleAppendWebhook = (nextTo: number) => {
    insert(nextTo, {
      id: undefined,
      url: "",
      label: "",
      isEnabled: false,
      isVerified: false,
      headers: [],
      isDeleted: false,
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
    <Box mb="80px">
      <Box my="16px">
        <Typography variant="h4" align="center">
          Webhook
        </Typography>
      </Box>

      <Table className="table table-bordered">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell>URL</HeaderTableCell>
            <HeaderTableCell>ラベル</HeaderTableCell>
            <HeaderTableCell />
            <HeaderTableCell>URL有効化</HeaderTableCell>
            <HeaderTableCell>削除</HeaderTableCell>
            <HeaderTableCell>追加</HeaderTableCell>
          </HeaderTableRow>
        </TableHead>
        <TableBody>
          {fields.map((field, index) => (
            <TableRow key={field.id}>
              {/* TODO show isAvailable ??? */}
              {/* TODO update webhook */}
              {field.isDeleted !== true && (
                <Fragment key={index}>
                  <TableCell>
                    <Controller
                      name={`webhooks.${index}.url`}
                      control={control}
                      defaultValue=""
                      render={({ field, fieldState: { error } }) => (
                        <TextField
                          {...field}
                          placeholder="URL"
                          error={error != null}
                          helperText={error?.message}
                          sx={{ width: "100%" }}
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
                          sx={{ width: "100%" }}
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
                      render={({ field, fieldState: { error } }) => (
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
                </Fragment>
              )}
            </TableRow>
          ))}
          {fields.filter((field) => !field.isDeleted).length === 0 && (
            <TableRow>
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
            </TableRow>
          )}
        </TableBody>
      </Table>
      <WebhookHeadersModal
        webhookIndex={openModalIndex}
        handleCloseModal={handleCloseModal}
        control={control}
      />
    </Box>
  );
};
