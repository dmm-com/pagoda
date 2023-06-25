import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  Button,
  IconButton,
  Modal,
  Table,
  TableBody,
  TableCell,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useEffect, useState } from "react";
import { Control, Controller, useFieldArray, useWatch } from "react-hook-form";

import { Schema } from "./EntityFormSchema";

const StyledModal = styled(Modal)(({}) => ({
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
}));

const Paper = styled(Box)(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  border: "2px solid #000",
  boxShadow: theme.shadows[5],
  padding: theme.spacing(2, 4, 3),
  width: "50%",
}));

interface Props {
  webhookIndex: number;
  handleCloseModal: () => void;
  control: Control<Schema>;
}

export const WebhookHeadersModal: FC<Props> = ({
  webhookIndex,
  handleCloseModal,
  control,
}) => {
  const { fields, insert, remove, replace } = useFieldArray({
    control,
    name: `webhooks.${webhookIndex}.headers`,
  });

  // NOTE initialize headers values manually with useWatch()
  // the useFieldArray() call in this component cannot resolve the initial value, so it does such thing...
  (() => {
    const [initialized, setInitialized] = useState(false);

    const headers = useWatch({
      control,
      name: `webhooks.${webhookIndex}.headers`,
    });

    useEffect(() => {
      // get only valid headers. useWatch will get incomplete values.
      if (!initialized && Array.isArray(headers)) {
        replace(headers);
        setInitialized(true);
      }
    }, [headers]);

    // enable to re-initialize on changing a webhook
    useEffect(() => {
      setInitialized(false);
    }, [webhookIndex]);
  })();

  const handleAppendWebhookAdditionalHeader = (nextTo: number) => {
    insert(nextTo, {
      headerKey: "",
      headerValue: "",
    });
  };

  const handleDeleteWebhookAdditionalHeader = (index: number) => {
    remove(index);
  };

  return (
    <StyledModal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      open={webhookIndex >= 0}
      onClose={handleCloseModal}
    >
      <Paper>
        <Typography variant={"h6"}>AdditionalHeader (Optional)</Typography>
        <Typography variant={"caption"}>
          指定した endpoint URL
          に送るリクエストに付加するヘッダ情報を入力してください。
        </Typography>
        <Table className="table">
          <TableBody>
            {fields.length === 0 && (
              <TableRow>
                <TableCell sx={{ p: "4px 8px 0px 0px", borderBottom: "0px" }}>
                  <TextField
                    label="Key"
                    variant="standard"
                    fullWidth={true}
                    disabled={true}
                    onClick={() => handleAppendWebhookAdditionalHeader(0)}
                  />
                </TableCell>
                <TableCell sx={{ p: "4px 8px 0px 0px", borderBottom: "0px" }}>
                  <TextField
                    label="Value"
                    variant="standard"
                    fullWidth={true}
                    disabled={true}
                    onClick={() => handleAppendWebhookAdditionalHeader(0)}
                  />
                </TableCell>
                <TableCell sx={{ borderBottom: "0px" }}>
                  <IconButton disabled={true}>
                    <DeleteOutlineIcon />
                  </IconButton>
                </TableCell>
                <TableCell sx={{ borderBottom: "0px" }}>
                  <IconButton
                    onClick={() => handleAppendWebhookAdditionalHeader(0)}
                  >
                    <AddIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            )}
            {fields.map((field, index) => (
              <TableRow key={field.id}>
                <TableCell sx={{ p: "4px 8px 0px 0px", borderBottom: "0px" }}>
                  <Controller
                    name={`webhooks.${webhookIndex}.headers.${index}.headerKey`}
                    control={control}
                    defaultValue=""
                    render={({ field, fieldState: { error } }) => (
                      <TextField
                        {...field}
                        label="Key"
                        variant="standard"
                        fullWidth={true}
                        error={error != null}
                        helperText={error?.message}
                        sx={{ width: "100%" }}
                      />
                    )}
                  />
                </TableCell>
                <TableCell sx={{ p: "4px 8px 0px 0px", borderBottom: "0px" }}>
                  <Controller
                    name={`webhooks.${webhookIndex}.headers.${index}.headerValue`}
                    control={control}
                    defaultValue=""
                    render={({ field, fieldState: { error } }) => (
                      <TextField
                        {...field}
                        label="Value"
                        variant="standard"
                        fullWidth={true}
                        error={error != null}
                        helperText={error?.message}
                        sx={{ width: "100%" }}
                      />
                    )}
                  />
                </TableCell>

                <TableCell sx={{ borderBottom: "0px" }}>
                  <IconButton
                    onClick={() => handleDeleteWebhookAdditionalHeader(index)}
                  >
                    <DeleteOutlineIcon />
                  </IconButton>
                </TableCell>

                <TableCell sx={{ borderBottom: "0px" }}>
                  <IconButton
                    onClick={() =>
                      handleAppendWebhookAdditionalHeader(index + 1)
                    }
                  >
                    <AddIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <Box sx={{ width: "92%" }}>
          <Button onClick={handleCloseModal}>
            <Typography align="right">閉じる</Typography>
          </Button>
        </Box>
      </Paper>
    </StyledModal>
  );
};
