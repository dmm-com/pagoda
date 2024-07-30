import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import KeyboardArrowUpRoundedIcon from "@mui/icons-material/KeyboardArrowUpRounded";
import {
  Box,
  Chip,
  Container,
  Fab,
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
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { AttributeValueField } from "components/entry/entryForm/AttributeValueField";
import { Schema } from "components/entry/entryForm/EntryFormSchema";

const ChipBox = styled(Box)(({}) => ({
  display: "flex",
  flexWrap: "wrap",
  gap: "12px",
  marginBottom: "20px",
}));

const StyledTableCell = styled(TableCell)(({}) => ({
  /* an anchor link adjusted fixed headers etc. */
  scrollMarginTop: "180px",
  padding: "8px 16px",
}));

const StyledTypography = styled(Typography)(({}) => ({
  flexGrow: 1,
}));

const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({}) => ({
  color: "#FFFFFF",
  width: "384px",
}));

const TableBox = styled(Box)(({}) => ({
  display: "flex",
  alignItems: "center",
}));

const RequiredLabel = styled(Typography)(({}) => ({
  border: "0.5px solid gray",
  borderRadius: 16,
  color: "white",
  backgroundColor: "gray",
  padding: "0 8px",
}));

const BottomBox = styled(Box)(({}) => ({
  display: "flex",
  justifyContent: "flex-end",
  margin: "12px 0",
  marginBottom: "100px",
}));

export interface EntryFormProps {
  entity: EntityDetail;
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
}

export const EntryForm: FC<EntryFormProps> = ({
  entity,
  control,
  setValue,
}) => {
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <Container>
      <ChipBox>
        <Chip
          id={"chip_name"}
          component="a"
          href={`#name`}
          icon={<ArrowDropDownIcon />}
          label="アイテム名"
          clickable={true}
          variant="outlined"
        />
        {entity.attrs.map(({ id, name }) => (
          <Chip
            key={id}
            id={`chip_${name}`}
            component="a"
            href={`#attrs-${name}`}
            icon={<ArrowDropDownIcon />}
            label={name}
            clickable={true}
            variant="outlined"
          />
        ))}
      </ChipBox>
      <Table id="table_attr_list">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell>項目</HeaderTableCell>
            <HeaderTableCell>内容</HeaderTableCell>
          </HeaderTableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <StyledTableCell>
              <TableBox>
                <StyledTypography id="name">アイテム名</StyledTypography>
                <RequiredLabel>必須</RequiredLabel>
              </TableBox>
            </StyledTableCell>
            <StyledTableCell>
              <Controller
                name="name"
                control={control}
                defaultValue=""
                render={({ field, fieldState: { error } }) => (
                  <TextField
                    {...field}
                    id="entry-name"
                    variant="standard"
                    error={error != null}
                    helperText={error?.message}
                    fullWidth
                  />
                )}
              />
            </StyledTableCell>
          </TableRow>
          {entity.attrs
            .sort((a, b) => a.index - b.index)
            .map(({ id, name, type, isMandatory, isWritable }) => (
              <TableRow key={id}>
                <StyledTableCell id={`attrs-${name}`}>
                  <TableBox>
                    <StyledTypography>{name}</StyledTypography>
                    {isMandatory && <RequiredLabel>必須</RequiredLabel>}
                  </TableBox>
                </StyledTableCell>
                <StyledTableCell>
                  {isWritable ? (
                    <AttributeValueField
                      control={control}
                      setValue={setValue}
                      type={type}
                      schemaId={id}
                    />
                  ) : (
                    <Typography>Permission denied.</Typography>
                  )}
                </StyledTableCell>
              </TableRow>
            ))}
        </TableBody>
      </Table>
      <BottomBox>
        <Fab id="scroll_button" color="primary" onClick={scrollToTop}>
          <KeyboardArrowUpRoundedIcon />
        </Fab>
      </BottomBox>
    </Container>
  );
};
