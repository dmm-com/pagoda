import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import { IconButton, TableCell, TableRow } from "@mui/material";
import React, { FC } from "react";
import { Control, useFieldArray } from "react-hook-form";

import { Condition } from "./Condition";
import { Schema } from "./TriggerFormSchema";

interface Props {
  control: Control<Schema>;
  entity: EntityDetail;
}

export const Conditions: FC<Props> = ({ control, entity }) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: "conditions",
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  const handleAppendCondition = (index: number) => {
    insert(index, {
      id: 0,
      attr: {
        id: 0,
        name: "",
        type: 0,
      },
      strCond: "",
      refCond: null,
      boolCond: undefined,
    });
  };

  return (
    <>
      {fields.map((condField, index) => (
        <Condition
          key={condField.key}
          index={index}
          control={control}
          remove={remove}
          handleAppendCondition={handleAppendCondition}
          entity={entity}
        />
      ))}
      {fields.length === 0 && (
        <TableRow>
          <TableCell />
          <TableCell />
          <TableCell />
          <TableCell>
            <IconButton onClick={() => handleAppendCondition(0)}>
              <AddIcon />
            </IconButton>
          </TableCell>
        </TableRow>
      )}
    </>
  );
};
