import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import KeyboardArrowUpRoundedIcon from "@mui/icons-material/KeyboardArrowUpRounded";
import {
  Box,
  Button,
  Container,
  Fab,
  Input,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import React, { FC } from "react";

import { EditableEntry, EditableEntryAttrs } from "./entryForm/EditableEntry";

import { EditAttributeValue } from "components/entry/entryForm/EditAttributeValue";
import { DjangoContext } from "utils/DjangoContext";

interface Props {
  entryInfo: EditableEntry;
  setEntryInfo: React.Dispatch<React.SetStateAction<EditableEntry>>;
}

export const EntryForm: FC<Props> = ({ entryInfo, setEntryInfo }) => {
  const djangoContext = DjangoContext.getInstance();

  const changeName = (name: string) => {
    setEntryInfo({
      ...entryInfo,
      name: name,
    });
  };

  const changeAttributes = (attrs: Record<string, EditableEntryAttrs>) => {
    setEntryInfo({
      ...entryInfo,
      attrs: attrs,
    });
  };

  const handleChangeAttribute = (name: string, attrType: number, valueInfo) => {
    switch (attrType) {
      case djangoContext.attrTypeValue.date:
      case djangoContext.attrTypeValue.string:
      case djangoContext.attrTypeValue.text:
        entryInfo.attrs[name].value.asString = valueInfo.value;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.boolean:
        entryInfo.attrs[name].value.asBoolean = valueInfo.checked;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.object:
        entryInfo.attrs[name].value.asObject = valueInfo.value;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.group:
        entryInfo.attrs[name].value.asGroup = valueInfo.value;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.named_object:
        if (valueInfo?.key !== undefined) {
          entryInfo.attrs[name].value.asNamedObject = {
            [valueInfo.key]:
              Object.values(
                entryInfo.attrs[name].value.asNamedObject ?? {}
              )[0] ?? null,
          };
        } else {
          entryInfo.attrs[name].value.asNamedObject = {
            [Object.keys(entryInfo.attrs[name].value.asNamedObject ?? {})[0] ??
            ""]: valueInfo.value,
          };
        }
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_string:
        if (entryInfo.attrs[name].value?.asArrayString == null) {
          entryInfo.attrs[name].value.asArrayString = [];
        }
        entryInfo.attrs[name].value.asArrayString[valueInfo.index] =
          valueInfo.value;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_object:
        entryInfo.attrs[name].value.asArrayObject = valueInfo.value;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_group:
        entryInfo.attrs[name].value.asArrayGroup = valueInfo.value;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_named_object:
        if (
          entryInfo.attrs[name].value.asArrayNamedObject.length <=
          valueInfo.index
        ) {
          entryInfo.attrs[name].value.asArrayNamedObject.push({ "": null });
          changeAttributes({ ...entryInfo.attrs });
          break;
        }

        if (valueInfo?.key !== undefined) {
          entryInfo.attrs[name].value.asArrayNamedObject[valueInfo.index] = {
            [valueInfo.key]:
              Object.values(
                entryInfo.attrs[name].value.asArrayNamedObject[valueInfo.index]
              )[0] ?? null,
          };
        } else {
          entryInfo.attrs[name].value.asArrayNamedObject[valueInfo.index] = {
            [Object.keys(
              entryInfo.attrs[name].value.asArrayNamedObject[valueInfo.index]
            )[0] ?? ""]: valueInfo.value,
          };
        }

        changeAttributes({ ...entryInfo.attrs });
        break;
    }
  };

  const handleClickDeleteListItem = (attrName: string, index?: number) => {
    const attrType = entryInfo.attrs[attrName].type;
    if (index !== undefined) {
      switch (attrType) {
        case djangoContext.attrTypeValue.array_string:
          entryInfo.attrs[attrName].value.asArrayString.splice(index, 1);
          break;
        case djangoContext.attrTypeValue.array_object:
          entryInfo.attrs[attrName].value.asArrayObject.splice(index, 1);
          break;
        case djangoContext.attrTypeValue.array_named_object:
          entryInfo.attrs[attrName].value.asArrayNamedObject.splice(index, 1);
          break;
        case djangoContext.attrTypeValue.array_group:
          entryInfo.attrs[attrName].value.asArrayGroup.splice(index, 1);
          break;
        default:
          throw new Error(`${attrType} is not array-like type`);
      }
      changeAttributes({ ...entryInfo.attrs });
    }
  };

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <Container sx={{ mb: "100px" }}>
      <Box my="40px" display="flex" flexWrap="wrap">
        <Box m="8px">
          <Button
            href="#name"
            sx={{
              border: "0.5px solid gray",
              borderRadius: 16,
              textTransform: "none",
            }}
          >
            <Typography sx={{ color: "black" }}>エントリ名</Typography>
            <ArrowDropDownIcon sx={{ color: "black", padding: "0 4px" }} />
          </Button>
        </Box>
        {Object.keys(entryInfo.attrs).map((attributeName) => (
          <Box key={attributeName} m="8px">
            <Button
              href={`#attrs-${attributeName}`}
              sx={{
                border: "0.5px solid gray",
                borderRadius: 16,
                textTransform: "none",
              }}
            >
              <Typography sx={{ color: "black", padding: "0 4px" }}>
                {attributeName}
              </Typography>
              <ArrowDropDownIcon sx={{ color: "black" }} />
            </Button>
          </Box>
        ))}
      </Box>
      <Table>
        <TableHead>
          <TableRow sx={{ backgroundColor: "#455A64" }} id="name">
            <TableCell sx={{ color: "#FFFFFF", width: "384px" }}>
              項目
            </TableCell>
            <TableCell sx={{ color: "#FFFFFF", width: "768px" }}>
              内容
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>
              <Box display="flex" alignItems="center">
                <Typography flexGrow={1}>エントリ名</Typography>
                <Typography
                  sx={{
                    border: "0.5px solid gray",
                    borderRadius: 16,
                    color: "white",
                    backgroundColor: "gray",
                    padding: "0 8px",
                  }}
                >
                  必須
                </Typography>
              </Box>
            </TableCell>
            <TableCell>
              <Input
                type="text"
                defaultValue={entryInfo.name}
                onChange={(e) => changeName(e.target.value)}
                fullWidth
                error={entryInfo.name === ""}
              />
            </TableCell>
          </TableRow>
          {Object.keys(entryInfo.attrs).map((attributeName, index) => (
            <TableRow key={index} id={`attrs-${attributeName}`}>
              <TableCell>
                <Box display="flex" alignItems="center">
                  <Typography flexGrow={1}>{attributeName}</Typography>
                  {entryInfo.attrs[attributeName]?.isMandatory && (
                    <Typography
                      sx={{
                        border: "0.5px solid gray",
                        borderRadius: 16,
                        color: "white",
                        backgroundColor: "gray",
                        padding: "0 8px",
                      }}
                    >
                      必須
                    </Typography>
                  )}
                </Box>
              </TableCell>
              <TableCell>
                <EditAttributeValue
                  attrName={attributeName}
                  attrInfo={entryInfo.attrs[attributeName]}
                  handleChangeAttribute={handleChangeAttribute}
                  handleClickDeleteListItem={handleClickDeleteListItem}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <Box display="flex" justifyContent="flex-end" my="12px">
        <Fab color="primary" onClick={scrollToTop}>
          <KeyboardArrowUpRoundedIcon />
        </Fab>
      </Box>
    </Container>
  );
};
