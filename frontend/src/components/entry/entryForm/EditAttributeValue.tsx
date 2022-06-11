import {
  Button,
  Box,
  Card,
  Checkbox,
  FormControlLabel,
  Grid,
  Input,
  List,
  ListItem,
  Radio,
  RadioGroup,
  Typography,
  TextField,
} from "@mui/material";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { DesktopDatePicker } from "@mui/x-date-pickers/DesktopDatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import React, { FC, useMemo } from "react";
import { useAsync } from "react-use";

import { getAttrReferrals } from "../../../utils/AironeAPIClient";
import { AutoCompletedField } from "../../common/AutoCompletedField";

import {
  EditableEntryAttrs,
  EditableEntryAttrValueGroup,
  EditableEntryAttrValueNamedObject,
  EditableEntryAttrValueObject,
} from "./EditableEntry";

import { DjangoContext } from "utils/DjangoContext";

interface CommonProps {
  attrName: string;
  attrType: number;
  index?: number;
  handleChange: (e: any, attrName: string, valueInfo: any) => void;
}

const ElemString: FC<
  CommonProps & {
    attrValue: string;
    handleClickDeleteListItem: (attrName: string, index?: number) => void;
  }
> = ({
  attrName,
  attrValue,
  attrType,
  index,
  handleChange,
  handleClickDeleteListItem,
}) => {
  return (
    <Box display="flex">
      <Input
        type="text"
        value={attrValue}
        onChange={(e) =>
          handleChange(e, attrName, {
            type: attrType,
            index: index,
            value: e.target.value,
          })
        }
        fullWidth
      />
      {index !== undefined && (
        <Grid item>
          <Button
            variant="outlined"
            onClick={() => handleClickDeleteListItem(attrName, index)}
          >
            del
          </Button>
        </Grid>
      )}
    </Box>
  );
};

const ElemBool: FC<CommonProps & { attrValue: boolean }> = ({
  attrName,
  attrValue,
  attrType,
  handleChange,
}) => {
  return (
    <Checkbox
      checked={attrValue}
      onChange={(e) =>
        handleChange(e, attrName, {
          type: attrType,
          index: undefined,
          checked: e.target.checked,
        })
      }
    />
  );
};

const ElemObject: FC<
  CommonProps & {
    attrId: number;
    attrValue: EditableEntryAttrValueObject;
    handleNarrowDownEntries: (
      e: any,
      attrId: number,
      attrName: string,
      attrType: number
    ) => void;
    handleClickDeleteListItem: (attrName: string, index?: number) => void;
    multiple?: boolean;
  }
> = ({
  attrId,
  attrName,
  attrValue,
  attrType,
  index,
  handleChange,
  handleNarrowDownEntries,
  handleClickDeleteListItem,
  multiple,
}) => {
  // FIXME Implement and use API V2
  // TODO call it reactively to avoid loading API???
  const referrals = useAsync(async () => {
    const resp = await getAttrReferrals(attrId);
    const data = await resp.json();
    return data.results;
  });

  const defaultValue = useMemo(() => {
    const matched = referrals.value?.filter((e) =>
      attrValue.map((e) => e.id).includes(e.id)
    );
    return matched ? (multiple ? matched : matched[0]) : undefined;
  }, [referrals.value, attrValue]);

  return (
    <Box>
      <Typography>エントリを選択</Typography>
      <Box display="flex" alignItems="center">
        {!referrals.loading && (
          <AutoCompletedField
            options={referrals.value ?? []}
            getOptionLabel={(option: { id: number; name: string }) =>
              option.name
            }
            defaultValue={defaultValue}
            handleChangeSelectedValue={(
              value:
                | { id: number; name: string }
                | { id: number; name: string }[]
            ) => {
              if (Array.isArray(value)) {
                // FIXME call handleChange
                // It will need to modify type of attribute state
              } else {
                handleChange(null, attrName, {
                  type: attrType,
                  index: index,
                  id: value.id,
                  name: value.name,
                  checked: true,
                });
              }
            }}
            multiple={multiple}
          />
        )}
        {index !== undefined && (
          <Button
            variant="outlined"
            onClick={() => handleClickDeleteListItem(attrName, index)}
          >
            del
          </Button>
        )}
      </Box>
    </Box>
  );
};

const ElemNamedObject: FC<
  CommonProps & {
    attrId: number;
    attrValue: EditableEntryAttrValueNamedObject;
    handleNarrowDownEntries: (
      e: any,
      attrId: number,
      attrName: string,
      attrType: number
    ) => void;
    handleClickDeleteListItem: (attrName: string, index?: number) => void;
  }
> = ({
  attrId,
  attrName,
  attrValue,
  attrType,
  index,
  handleChange,
  handleNarrowDownEntries,
  handleClickDeleteListItem,
}) => {
  const key = Object.keys(attrValue)[0];
  return (
    <Box display="flex">
      <Box>
        <Typography>name</Typography>
        <Input
          type="text"
          value={key}
          onChange={(e) =>
            handleChange(e, attrName, {
              type: attrType,
              index: index,
              key: e.target.value,
            })
          }
        />
      </Box>
      <ElemObject
        attrId={attrId}
        attrName={attrName}
        attrValue={attrValue[key]}
        attrType={attrType}
        index={index}
        handleChange={handleChange}
        handleNarrowDownEntries={handleNarrowDownEntries}
        handleClickDeleteListItem={handleClickDeleteListItem}
      />
    </Box>
  );
};

const ElemGroup: FC<
  CommonProps & {
    attrValue: EditableEntryAttrValueGroup;
    handleNarrowDownGroups: (
      e: any,
      attrName: string,
      attrType: number
    ) => void;
    handleClickDeleteListItem?: (attrName: string, index?: number) => void;
  }
> = ({
  attrName,
  attrValue,
  attrType,
  index,
  handleChange,
  handleNarrowDownGroups,
  handleClickDeleteListItem,
}) => {
  return (
    <Grid container>
      <Grid item>
        <Card variant="outlined">
          <RadioGroup aria-label="group" name="radio-buttons-group">
            {attrValue.map((value) => (
              <FormControlLabel
                key={value.id}
                control={<Radio checked={value.checked} />}
                label={value.name}
                onChange={(e, checked) =>
                  handleChange(e, attrName, {
                    type: attrType,
                    index: index,
                    id: value.id,
                    name: value.name,
                    checked: checked,
                  })
                }
              />
            ))}
          </RadioGroup>
          <Input
            placeholder="グループ名で絞り込む"
            onChange={(e) => {
              handleNarrowDownGroups(e, attrName, attrType);
            }}
            onClick={(e) => {
              handleNarrowDownGroups(e, attrName, attrType);
            }}
          />
        </Card>
      </Grid>
      {handleClickDeleteListItem && (
        <Grid item>
          <Button
            variant="outlined"
            onClick={() => handleClickDeleteListItem(attrName, index)}
          >
            del
          </Button>
        </Grid>
      )}
    </Grid>
  );
};

const ElemDate: FC<
  CommonProps & {
    attrValue: string;
    handleClickDeleteListItem: (attrName: string, index?: number) => void;
  }
> = ({ attrName, attrValue, attrType, handleChange }) => {
  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <DesktopDatePicker
        label="月日を選択"
        inputFormat="yyyy/MM/dd"
        value={new Date(attrValue)}
        onChange={(date: Date) => {
          handleChange(null, attrName, {
            type: attrType,
            value: `${date.getFullYear()}/${
              date.getMonth() + 1
            }/${date.getDate()}`,
          });
        }}
        renderInput={(params) => <TextField {...params} />}
      />
    </LocalizationProvider>
  );
};

interface Props {
  attrName: string;
  attrInfo: EditableEntryAttrs;
  handleChangeAttribute: (e: any, attrName: string, valueInfo: any) => void;
  handleNarrowDownEntries: (
    e: any,
    attrId: number,
    attrName: string,
    attrType: number
  ) => void;
  handleNarrowDownGroups: (e: any, attrName: string, attrType: number) => void;
  handleClickDeleteListItem: (attrName: string, index?: number) => void;
}

export const EditAttributeValue: FC<Props> = ({
  attrName,
  attrInfo,
  handleChangeAttribute,
  handleNarrowDownEntries,
  handleNarrowDownGroups,
  handleClickDeleteListItem,
}) => {
  const djangoContext = DjangoContext.getInstance();

  const handleClickAddListItem = (e, value) => {
    const index = (() => {
      switch (attrInfo.type) {
        case djangoContext.attrTypeValue.array_string:
          return attrInfo.value.asArrayString.length;
        case djangoContext.attrTypeValue.array_object:
          return attrInfo.value.asArrayObject.length;
        case djangoContext.attrTypeValue.array_named_object:
          return attrInfo.value.asArrayNamedObject.length;
        case djangoContext.attrTypeValue.array_group:
          return attrInfo.value.asArrayGroup.length;
        default:
          throw new Error(`${attrInfo.type} is not array-like type`);
      }
    })();
    handleChangeAttribute(e, attrName, {
      type: attrInfo.type,
      index: index,
      value: value,
    });
  };

  switch (attrInfo.type) {
    case djangoContext.attrTypeValue.object:
      return (
        <ElemObject
          attrId={attrInfo.id}
          attrName={attrName}
          attrValue={[{ ...attrInfo.value.asObject, checked: false }]}
          attrType={attrInfo.type}
          handleChange={handleChangeAttribute}
          handleNarrowDownEntries={handleNarrowDownEntries}
          handleClickDeleteListItem={handleClickDeleteListItem}
        />
      );

    case djangoContext.attrTypeValue.boolean:
      return (
        <ElemBool
          attrName={attrName}
          attrValue={attrInfo.value.asBoolean}
          attrType={attrInfo.type}
          handleChange={handleChangeAttribute}
        />
      );

    case djangoContext.attrTypeValue.string:
    case djangoContext.attrTypeValue.text:
      return (
        <ElemString
          attrName={attrName}
          attrValue={attrInfo.value.asString}
          attrType={attrInfo.type}
          handleChange={handleChangeAttribute}
          handleClickDeleteListItem={handleClickDeleteListItem}
        />
      );

    case djangoContext.attrTypeValue.date:
      return (
        <ElemDate
          attrName={attrName}
          attrValue={attrInfo.value.asString}
          attrType={attrInfo.type}
          handleChange={handleChangeAttribute}
          handleClickDeleteListItem={handleClickDeleteListItem}
        />
      );

    case djangoContext.attrTypeValue.named_object:
      return (
        <ElemNamedObject
          attrId={attrInfo.id}
          attrName={attrName}
          attrValue={attrInfo.value.asNamedObject}
          attrType={attrInfo.type}
          handleChange={handleChangeAttribute}
          handleNarrowDownEntries={handleNarrowDownEntries}
          handleClickDeleteListItem={handleClickDeleteListItem}
        />
      );

    case djangoContext.attrTypeValue.array_object:
      return (
        <Box>
          <Button
            variant="contained"
            color="primary"
            onClick={(e) => handleClickAddListItem(e, [])}
          >
            add
          </Button>
          <List>
            {attrInfo.value.asArrayObject.map((info, n) => (
              <ListItem key={n}>
                <ElemObject
                  attrId={attrInfo.id}
                  attrName={attrName}
                  attrValue={info}
                  attrType={attrInfo.type}
                  index={n}
                  handleChange={handleChangeAttribute}
                  handleNarrowDownEntries={handleNarrowDownEntries}
                  handleClickDeleteListItem={handleClickDeleteListItem}
                  multiple
                />
              </ListItem>
            ))}
          </List>
        </Box>
      );

    case djangoContext.attrTypeValue.array_string:
      return (
        <Box>
          <Button
            variant="contained"
            color="primary"
            onClick={(e) => handleClickAddListItem(e, "")}
          >
            add
          </Button>
          <List>
            {attrInfo.value.asArrayString.map((info, n) => (
              <ListItem key={n}>
                <ElemString
                  attrName={attrName}
                  attrValue={info}
                  attrType={attrInfo.type}
                  index={n}
                  handleChange={handleChangeAttribute}
                  handleClickDeleteListItem={handleClickDeleteListItem}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      );

    case djangoContext.attrTypeValue.array_named_object:
      return (
        <Box>
          <Button
            variant="contained"
            color="primary"
            onClick={(e) => handleClickAddListItem(e, { "": [] })}
          >
            add
          </Button>
          <List>
            {attrInfo.value.asArrayNamedObject.map((info, n) => (
              <ListItem key={n}>
                <ElemNamedObject
                  attrId={attrInfo.id}
                  attrName={attrName}
                  attrValue={info}
                  attrType={attrInfo.type}
                  index={n}
                  handleChange={handleChangeAttribute}
                  handleNarrowDownEntries={handleNarrowDownEntries}
                  handleClickDeleteListItem={handleClickDeleteListItem}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      );

    case djangoContext.attrTypeValue.array_group:
      return (
        <Box>
          <Button
            variant="contained"
            color="primary"
            onClick={(e) => handleClickAddListItem(e, [])}
          >
            add
          </Button>
          <List>
            {attrInfo.value.asArrayGroup.map((info, n) => (
              <ListItem key={n}>
                <ElemGroup
                  attrName={attrName}
                  attrValue={info}
                  attrType={attrInfo.type}
                  index={n}
                  handleChange={handleChangeAttribute}
                  handleNarrowDownGroups={handleNarrowDownGroups}
                  handleClickDeleteListItem={handleClickDeleteListItem}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      );

    case djangoContext.attrTypeValue.group:
      return (
        <ElemGroup
          attrName={attrName}
          attrValue={attrInfo.value.asGroup}
          attrType={attrInfo.type}
          handleChange={handleChangeAttribute}
          handleNarrowDownGroups={handleNarrowDownGroups}
        />
      );
  }
};
