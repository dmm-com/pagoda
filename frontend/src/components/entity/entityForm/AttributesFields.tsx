import { Entity } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";
import { Control, useFieldArray } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { AttributeField } from "./AttributeField";
import { Schema } from "./EntityFormSchema";

import { AttributeTypes } from "services/Constants";

const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({}) => ({
  color: "#FFFFFF",
  boxSizing: "border-box",
}));

const StyledTableBody = styled(TableBody)({
  "tr:nth-of-type(odd)": {
    backgroundColor: "white",
  },
  "tr:nth-of-type(even)": {
    backgroundColor: "#607D8B0A",
  },
  "& td": {
    padding: "8px",
  },
});

const HighlightedTableRow = styled(TableRow)(({}) => ({
  "@keyframes highlighted": {
    from: {
      backgroundColor: "#6B8998",
    },
  },
  animation: "highlighted 1s ease 0s 1",
}));

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  referralEntities: Entity[];
}

export const AttributesFields: FC<Props> = ({
  control,
  setValue,
  referralEntities,
}) => {
  const { fields, insert, remove, swap } = useFieldArray({
    control,
    name: "attrs",
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  const [latestChangedIndex, setLatestChangedIndex] = useState<number | null>(
    null,
  );

  const handleAppendAttribute = (index: number) => {
    insert(index + 1, {
      name: "",
      type: AttributeTypes.string.type,
      isMandatory: false,
      isDeleteInChain: false,
      isSummarized: false,
      isWritable: true,
      referral: [],
      note: "",
    });
  };

  const handleDeleteAttribute = (index: number) => {
    remove(index);
  };

  const handleChangeOrderAttribute = (index: number, order: number) => {
    const newIndex = index - order;
    swap(newIndex, index);
    setLatestChangedIndex(newIndex);
  };

  return (
    <>
      <Typography variant="h4" align="center" my="16px">
        属性情報
      </Typography>

      <Table id="table_attribute_list">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell width="300px">属性名</HeaderTableCell>
            <HeaderTableCell width="100px">属性説明</HeaderTableCell>
            <HeaderTableCell width="300px">型</HeaderTableCell>
            <HeaderTableCell width="100px">必須</HeaderTableCell>
            <HeaderTableCell width="100px">関連削除</HeaderTableCell>
            <HeaderTableCell width="100px">並び替え</HeaderTableCell>
            <HeaderTableCell width="100px">削除</HeaderTableCell>
            <HeaderTableCell width="100px">追加</HeaderTableCell>
            <HeaderTableCell width="100px">ACL設定</HeaderTableCell>
          </HeaderTableRow>
        </TableHead>
        <StyledTableBody>
          <>
            {fields.map((field, index) => {
              const StyledTableRow =
                index === latestChangedIndex ? HighlightedTableRow : TableRow;
              return (
                <StyledTableRow key={field.key}>
                  <AttributeField
                    referralEntities={referralEntities}
                    handleAppendAttribute={handleAppendAttribute}
                    handleDeleteAttribute={handleDeleteAttribute}
                    handleChangeOrderAttribute={handleChangeOrderAttribute}
                    control={control}
                    setValue={setValue}
                    maxIndex={fields.length - 1}
                    attrId={field.id}
                    index={index}
                  />
                </StyledTableRow>
              );
            })}
            {fields.length === 0 && (
              <AttributeField
                referralEntities={referralEntities}
                handleAppendAttribute={handleAppendAttribute}
                handleDeleteAttribute={handleDeleteAttribute}
                handleChangeOrderAttribute={handleChangeOrderAttribute}
                control={control}
                setValue={setValue}
                maxIndex={0}
              />
            )}
          </>
        </StyledTableBody>
      </Table>
    </>
  );
};
