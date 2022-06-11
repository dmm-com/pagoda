import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import KeyboardArrowUpRoundedIcon from "@mui/icons-material/KeyboardArrowUpRounded";
import {
  Box,
  Button,
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

import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { EditAttributeValue } from "components/entry/entryForm/EditAttributeValue";
import { getAttrReferrals } from "utils/AironeAPIClient";
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

  const handleChangeAttribute = (event, name: string, valueInfo) => {
    switch (valueInfo.type) {
      case djangoContext.attrTypeValue.string:
      case djangoContext.attrTypeValue.date:
      case djangoContext.attrTypeValue.text:
        entryInfo.attrs[name].value.asString = valueInfo.value;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.boolean:
        entryInfo.attrs[name].value.asBoolean = valueInfo.checked;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.object:
        entryInfo.attrs[name].value.asObject = valueInfo;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.group:
        entryInfo.attrs[name].value.asGroup = entryInfo.attrs[
          name
        ].value.asGroup.map((x) => ({
          ...x,
          checked: x.id == valueInfo.id && valueInfo.checked,
        }));
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.named_object:
        const namedObjectKey = Object.keys(
          entryInfo.attrs[name].value.asNamedObject
        )[0];
        entryInfo.attrs[name].value.asNamedObject[namedObjectKey] =
          entryInfo.attrs[name].value.asNamedObject[namedObjectKey].map(
            (x) => ({
              ...x,
              checked: x.id == valueInfo.id && valueInfo.checked,
            })
          );
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_string:
        entryInfo.attrs[name].value.asArrayString[valueInfo.index] =
          valueInfo.value;
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_object:
        // In this case, new blank co-Attribute value will be added
        if (
          valueInfo.index >= entryInfo.attrs[name].value.asArrayObject.length
        ) {
          entryInfo.attrs[name].value.asArrayObject.push(valueInfo.value);
        } else {
          entryInfo.attrs[name].value.asArrayObject[valueInfo.index] =
            entryInfo.attrs[name].value.asArrayObject[valueInfo.index].map(
              (x) => ({
                ...x,
                checked: x.id == valueInfo.id && valueInfo.checked,
              })
            );
        }
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_group:
        // In this case, new blank co-Attribute value will be added
        if (
          valueInfo.index >= entryInfo.attrs[name].value.asArrayGroup.length
        ) {
          entryInfo.attrs[name].value.asArrayGroup.push(valueInfo.value);
        } else {
          entryInfo.attrs[name].value.asArrayGroup[valueInfo.index] =
            entryInfo.attrs[name].value.asArrayGroup[valueInfo.index].map(
              (x) => ({
                ...x,
                checked: x.id == valueInfo.id && valueInfo.checked,
              })
            );
        }
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_named_object:
        const arrayNamedObjectKey = Object.keys(
          entryInfo.attrs[name].value.asArrayNamedObject[valueInfo.index]
        )[0];
        entryInfo.attrs[name].value.asArrayNamedObject[valueInfo.index][
          arrayNamedObjectKey
        ] = entryInfo.attrs[name].value.asArrayNamedObject[valueInfo.index][
          arrayNamedObjectKey
        ].map((x) => ({
          ...x,
          checked: x.id == valueInfo.id && valueInfo.checked,
        }));
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

  // FIXME remove it??
  const handleNarrowDownGroups = async (
    e,
    attrName: string,
    attrType: number
  ) => {
    const refs = await aironeApiClientV2.getGroups();
    const userInputValue = e.target.value;

    const _getUpdatedValues = (currentValue) => {
      return refs
        .filter(
          (r) =>
            r.name.includes(userInputValue) ||
            currentValue.find((x) => x.id === r.id && x.checked)
        )
        .map((r) => ({
          id: r.id,
          name: r.name,
          checked: currentValue.find((x) => x.id == r.id)?.checked === true,
        }));
    };

    switch (attrType) {
      case djangoContext.attrTypeValue.group:
        entryInfo.attrs[attrName].value.asGroup = _getUpdatedValues(
          entryInfo.attrs[attrName].value.asGroup
        );
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_group:
        entryInfo.attrs[attrName].value.asArrayGroup = entryInfo.attrs[
          attrName
        ].value.asArrayGroup.map((curr) => _getUpdatedValues(curr));
        changeAttributes({ ...entryInfo.attrs });
        break;
    }
  };

  const handleNarrowDownEntries = async (
    e,
    attrId: number,
    attrName: string,
    attrType: number
  ) => {
    const resp = await getAttrReferrals(attrId);
    const refs = await resp.json();
    const userInputValue = e.target.value;

    const _getUpdatedValues = (currentValue) => {
      return refs.results
        .filter(
          (r) =>
            r.name.includes(userInputValue) ||
            currentValue.find((x) => x.id === r.id && x.checked)
        )
        .map((r) => ({
          id: r.id,
          name: r.name,
          checked: currentValue.find((x) => x.id == r.id)?.checked === true,
        }));
    };

    switch (attrType) {
      case djangoContext.attrTypeValue.object:
        entryInfo.attrs[attrName].value.asObject = _getUpdatedValues(
          entryInfo.attrs[attrName].value.asObject
        );
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_object:
        entryInfo.attrs[attrName].value.asArrayObject = entryInfo.attrs[
          attrName
        ].value.asArrayObject.map((curr) => _getUpdatedValues(curr));
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.named_object:
        const attrKey = Object.keys(
          entryInfo.attrs[attrName].value.asNamedObject
        )[0];
        entryInfo.attrs[attrName].value.asNamedObject[attrKey] =
          _getUpdatedValues(
            entryInfo.attrs[attrName].value.asNamedObject[attrKey]
          );
        changeAttributes({ ...entryInfo.attrs });
        break;

      case djangoContext.attrTypeValue.array_named_object:
        entryInfo.attrs[attrName].value.asArrayNamedObject = entryInfo.attrs[
          attrName
        ].value.asArrayNamedObject.map((curr) => {
          const attrKey = Object.keys(curr)[0];
          return { [attrKey]: _getUpdatedValues(curr[attrKey]) };
        });
        changeAttributes({ ...entryInfo.attrs });
        break;
    }
  };

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <Box sx={{ mb: "100px" }}>
      <Box mb="40px" display="flex" flexWrap="wrap">
        <Box mx="4px" my="4px">
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
          <Box key={attributeName} mx="4px" my="4px">
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
            <TableCell sx={{ color: "#FFFFFF" }}>項目</TableCell>
            <TableCell sx={{ color: "#FFFFFF" }}>内容</TableCell>
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
                  handleNarrowDownEntries={handleNarrowDownEntries}
                  handleNarrowDownGroups={handleNarrowDownGroups}
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
    </Box>
  );
};
