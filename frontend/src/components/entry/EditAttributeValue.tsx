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
} from "@mui/material";
import React, { FC } from "react";

import { DjangoContext } from "../../utils/DjangoContext";

interface CommonProps {
  attrName: string;
  attrType: string;
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
    <Grid container>
      <Grid item>
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
        />
      </Grid>
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
    </Grid>
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
    attrValue: any;
    handleNarrowDownEntries: (
      e: any,
      attrId: number,
      attrName: string,
      attrType: string
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
  return (
    <Grid container>
      <Grid item>
        <Card variant="outlined">
          <RadioGroup aria-label="object" name="radio-buttons-group">
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
            placeholder="エントリ名で絞り込む"
            onChange={(e) => {
              handleNarrowDownEntries(e, attrId, attrName, attrType);
            }}
            onClick={(e) => {
              handleNarrowDownEntries(e, attrId, attrName, attrType);
            }}
          />
        </Card>
      </Grid>
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
    </Grid>
  );
};

const ElemNamedObject: FC<
  CommonProps & {
    attrId: number;
    attrValue: any;
    handleNarrowDownEntries: (
      e: any,
      attrId: number,
      attrName: string,
      attrType: string
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
    <>
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
    </>
  );
};

const ElemGroup: FC<
  CommonProps & {
    attrValue: any;
    handleNarrowDownGroups: (
      e: any,
      attrName: string,
      attrType: string
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

interface Props {
  attrName: string;
  attrInfo: any;
  handleChangeAttribute: (e: any, attrName: string, valueInfo: any) => void;
  handleNarrowDownEntries: (
    e: any,
    attrId: number,
    attrName: string,
    attrType: string
  ) => void;
  handleNarrowDownGroups: (e: any, attrName: string, attrType: string) => void;
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
    handleChangeAttribute(e, attrName, {
      type: attrInfo.type,
      index: attrInfo.value.length,
      value: value,
    });
  };

  switch (attrInfo.type) {
    case djangoContext.attrTypeValue.object:
      return (
        <ElemObject
          attrId={attrInfo.id}
          attrName={attrName}
          attrValue={attrInfo.value}
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
          attrValue={attrInfo.value}
          attrType={attrInfo.type}
          handleChange={handleChangeAttribute}
        />
      );

    case djangoContext.attrTypeValue.string:
    case djangoContext.attrTypeValue.text:
    case djangoContext.attrTypeValue.date:
      return (
        <ElemString
          attrName={attrName}
          attrValue={attrInfo.value}
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
          attrValue={attrInfo.value}
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
            {attrInfo.value.map((info, n) => (
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
            {attrInfo.value.map((info, n) => (
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
            {attrInfo.value.map((info, n) => (
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
            {attrInfo.value.map((info, n) => (
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
          attrValue={attrInfo.value}
          attrType={attrInfo.type}
          handleChange={handleChangeAttribute}
          handleNarrowDownGroups={handleNarrowDownGroups}
        />
      );
  }
};
