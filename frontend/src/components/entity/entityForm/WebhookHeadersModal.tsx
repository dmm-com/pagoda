import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  Button,
  IconButton,
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

import { AironeModal } from "../../common/AironeModal";

import { Schema } from "./EntityFormSchema";

const StyledTable = styled(Table)(({}) => ({
  "& td": {
    height: "72px",
    padding: "8px",
    verticalAlign: "top",
    borderBottom: "0px",
  },
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
    <AironeModal
      title={"AdditionalHeader (Optional)"}
      caption={
        "指定した endpoint URL に送るリクエストに付加するヘッダ情報を入力してください。"
      }
      open={webhookIndex >= 0}
      onClose={handleCloseModal}
    >
      <StyledTable className="table">
        <TableBody>
          {fields.length === 0 && (
            <TableRow>
              <TableCell>
                <TextField
                  label="Key"
                  variant="standard"
                  fullWidth
                  disabled
                  onClick={() => handleAppendWebhookAdditionalHeader(0)}
                />
              </TableCell>
              <TableCell>
                <TextField
                  label="Value"
                  variant="standard"
                  fullWidth
                  disabled
                  onClick={() => handleAppendWebhookAdditionalHeader(0)}
                />
              </TableCell>
              <TableCell>
                <IconButton disabled>
                  <DeleteOutlineIcon />
                </IconButton>
              </TableCell>
              <TableCell>
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
              <TableCell>
                <Controller
                  name={`webhooks.${webhookIndex}.headers.${index}.headerKey`}
                  control={control}
                  defaultValue=""
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      label="Key"
                      variant="standard"
                      fullWidth
                      error={error != null}
                      helperText={error?.message}
                    />
                  )}
                />
              </TableCell>
              <TableCell>
                <Controller
                  name={`webhooks.${webhookIndex}.headers.${index}.headerValue`}
                  control={control}
                  defaultValue=""
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      label="Value"
                      variant="standard"
                      fullWidth
                      error={error != null}
                      helperText={error?.message}
                    />
                  )}
                />
              </TableCell>

              <TableCell>
                <IconButton
                  onClick={() => handleDeleteWebhookAdditionalHeader(index)}
                >
                  <DeleteOutlineIcon />
                </IconButton>
              </TableCell>

              <TableCell>
                <IconButton
                  onClick={() => handleAppendWebhookAdditionalHeader(index + 1)}
                >
                  <AddIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </StyledTable>

      <Box sx={{ width: "92%" }}>
        <Button onClick={handleCloseModal}>
          <Typography align="right">閉じる</Typography>
        </Button>
      </Box>
    </AironeModal>
  );
};
