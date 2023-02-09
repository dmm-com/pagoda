import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import KeyboardArrowUpRoundedIcon from "@mui/icons-material/KeyboardArrowUpRounded";
import {
  Box,
  Button,
  Container,
  Fab,
  Input,
  Link,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import React, { Dispatch, FC, SetStateAction, useEffect } from "react";
import { useLocation } from "react-router-dom";

import { EditableEntry, EditableEntryAttrs } from "./entryForm/EditableEntry";

import { EditAttributeValue } from "components/entry/entryForm/EditAttributeValue";
import { DjangoContext } from "services/DjangoContext";
import { updateEntryInfoValueFromValueInfo } from "services/entry/Edit";

interface Props {
  entryInfo: EditableEntry;
  setEntryInfo: Dispatch<EditableEntry>;
  setIsAnchorLink: Dispatch<SetStateAction<boolean>>;
}

export const EntryForm: FC<Props> = ({
  entryInfo,
  setEntryInfo,
  setIsAnchorLink,
}) => {
  const djangoContext = DjangoContext.getInstance();
  const location = useLocation();

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

  const handleChangeAttribute = (
    attrName: string,
    attrType: number,
    valueInfo: any
  ) => {
    updateEntryInfoValueFromValueInfo(entryInfo, attrName, attrType, valueInfo);

    // Update entryInfo.attrs value depends on the changing values
    changeAttributes({ ...entryInfo.attrs });
  };

  const handleClickAddListItem = (
    attrName: string,
    attrType: number,
    index: number
  ) => {
    switch (attrType) {
      case djangoContext?.attrTypeValue.array_string:
        entryInfo.attrs[attrName].value.asArrayString?.splice(index + 1, 0, "");
        break;
      case djangoContext?.attrTypeValue.array_named_object:
        entryInfo.attrs[attrName].value.asArrayNamedObject?.splice(
          index + 1,
          0,
          // @ts-ignore
          { "": null }
        );
        break;
      default:
        throw new Error(`${attrType} is not array-like type`);
    }
    changeAttributes({ ...entryInfo.attrs });
  };

  const handleClickDeleteListItem = (
    attrName: string,
    attrType: number,
    index?: number
  ) => {
    if (index !== undefined) {
      switch (attrType) {
        case djangoContext?.attrTypeValue.array_string:
          entryInfo.attrs[attrName].value.asArrayString?.splice(index, 1);
          // auto-fill an empty element
          if (entryInfo.attrs[attrName].value.asArrayString?.length === 0) {
            entryInfo.attrs[attrName].value.asArrayString?.splice(
              index + 1,
              0,
              ""
            );
          }
          break;
        case djangoContext?.attrTypeValue.array_named_object:
          entryInfo.attrs[attrName].value.asArrayNamedObject?.splice(index, 1);
          // auto-fill an empty element
          if (
            entryInfo.attrs[attrName].value.asArrayNamedObject?.length === 0
          ) {
            entryInfo.attrs[attrName].value.asArrayNamedObject?.splice(
              index + 1,
              0,
              // @ts-ignore
              { "": null }
            );
          }
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

  useEffect(() => {
    setIsAnchorLink(false);
  }, [location]);

  return (
    <Container sx={{ mb: "100px" }}>
      <Box mb="20px" display="flex" flexWrap="wrap">
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
              onClick={() => setIsAnchorLink(true)}
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
          <TableRow sx={{ backgroundColor: "#455A64" }}>
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
                {/* an anchor link adjusted fixed headers etc. */}
                <Link
                  id="name"
                  sx={{ marginTop: "-500px", paddingTop: "500px" }}
                />
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
            <TableRow key={index}>
              <TableCell>
                <Box display="flex" alignItems="center">
                  {/* an anchor link adjusted fixed headers etc. */}
                  <Link
                    id={`attrs-${attributeName}`}
                    sx={{ marginTop: "-500px", paddingTop: "500px" }}
                  />
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
                  handleClickAddListItem={handleClickAddListItem}
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
