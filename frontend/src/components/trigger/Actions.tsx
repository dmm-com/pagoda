import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import { IconButton, TableCell, TableRow } from "@mui/material";
import React, { FC } from "react";
import { Control, useFieldArray } from "react-hook-form";

import { Action } from "./Action";
import { Schema } from "./TriggerFormSchema";

interface Props {
  control: Control<Schema>;
  entity: EntityDetail;
}

export const Actions: FC<Props> = ({ control, entity }) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: "actions",
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  const handleAppendAction = (index: number) => {
    insert(index + 1, {
      id: 0,
      attr: {
        id: 0,
        name: "",
        type: 0,
      },
      values: [
        {
          id: 0,
          strCond: "",
          refCond: null,
          boolCond: undefined,
        },
      ],
    });
  };

  return (
    <>
      {fields.map((actionField, index) => (
        <Action
          index={index}
          key={actionField.key}
          control={control}
          remove={remove}
          handleAppendAction={handleAppendAction}
          entity={entity}
        />
      ))}
      {fields.length === 0 && (
        <TableRow>
          <TableCell />
          <TableCell />
          <TableCell />
          <TableCell>
            <IconButton onClick={() => handleAppendAction(0)}>
              <AddIcon />
            </IconButton>
          </TableCell>
        </TableRow>
      )}
    </>
  );
};
