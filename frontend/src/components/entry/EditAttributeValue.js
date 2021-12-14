import { Button } from "@material-ui/core";
import Box from "@material-ui/core/Box";
import Card from "@material-ui/core/Card";
import Checkbox from "@material-ui/core/Checkbox";
import Grid from "@material-ui/core/Grid";
import FormControlLabel from "@material-ui/core/FormControlLabel";
import Input from "@material-ui/core/Input";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import Radio from "@material-ui/core/Radio";
import RadioGroup from "@material-ui/core/RadioGroup";
import PropTypes from "prop-types";
import React from "react";

import { DjangoContext } from "../../utils/DjangoContext";

function ElemString({ attrName, attrValue, attrType, index, handleChange }) {
  return (
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
  );
}

function ElemBool({ attrName, attrValue, attrType, handleChange }) {
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
}

function ElemObject({
  attrId,
  attrName,
  attrValue,
  attrType,
  index,
  handleChange,
  handleNarrowDownEntries,
  handleClickDeleteListItem,
}) {
  return (
    <Grid container>
      <Grid item>
        <Card variant="outlined">
          <RadioGroup aria-label="object" name="radio-buttons-group">
            {attrValue.map((value) => {
              return (
                <FormControlLabel
                  key={value.id}
                  control={<Radio checked={value.checked} />}
                  label={value.name}
                  onChange={(e) =>
                    handleChange(e, attrName, {
                      type: attrType,
                      index: index,
                      id: value.id,
                      name: value.name,
                      checked: e.target.checked,
                    })
                  }
                />
              );
            })}
          </RadioGroup>
          <Input
            text="text"
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
      <Grid item>
        <Button
          variant="outlined"
          onClick={(e) => handleClickDeleteListItem(e, attrName, index)}
        >
          del
        </Button>
      </Grid>
    </Grid>
  );
}

function ElemNamedObject({
  attrId,
  attrName,
  attrValue,
  attrType,
  index,
  handleChange,
  handleNarrowDownEntries,
  handleClickDeleteListItem,
}) {
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
}

function ElemGroup({
  attrName,
  attrValue,
  attrType,
  index,
  handleChange,
  handleNarrowDownGroups,
}) {
  //  return <a href={groupsPath()}>{attrValue.name}</a>;
  return (
    <Card variant="outlined">
      <RadioGroup aria-label="group" name="radio-buttons-group">
        {attrValue.map((value) => {
          return (
            <FormControlLabel
              key={value.id}
              control={<Radio checked={value.checked} />}
              label={value.name}
              onChange={(e) =>
                handleChange(e, attrName, {
                  type: attrType,
                  index: index,
                  id: value.id,
                  name: value.name,
                  checked: e.target.checked,
                })
              }
            />
          );
        })}
      </RadioGroup>

      <Input
        text="text"
        placeholder="グループ名で絞り込む"
        onChange={(e) => {
          handleNarrowDownGroups(e, attrName, attrType);
        }}
        onClick={(e) => {
          handleNarrowDownGroups(e, attrName, attrType);
        }}
      />
    </Card>
  );
}

export function EditAttributeValue({
  attrName,
  attrInfo,
  handleChangeAttribute,
  handleNarrowDownEntries,
  handleNarrowDownGroups,
  handleClickDeleteListItem,
}) {
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
            {attrInfo.value.map((info, n) => {
              return (
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
              );
            })}
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
            {attrInfo.value.map((info, n) => {
              return (
                <ListItem key={n}>
                  <ElemString
                    attrName={attrName}
                    attrValue={info}
                    attrType={attrInfo.type}
                    index={n}
                    handleChange={handleChangeAttribute}
                  />
                </ListItem>
              );
            })}
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
            {attrInfo.value.map((info, n) => {
              return (
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
              );
            })}
          </List>
        </Box>
      );

    case djangoContext.attrTypeValue.array_group:
      return (
        <List>
          {attrInfo.value.map((info, n) => {
            return (
              <ListItem key={n}>
                <ElemGroup
                  attrName={attrName}
                  attrValue={info}
                  attrType={attrInfo.type}
                  index={n}
                  handleChange={handleChangeAttribute}
                  handleNarrowDownGroups={handleNarrowDownGroups}
                />
              </ListItem>
            );
          })}
        </List>
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
}

EditAttributeValue.propTypes = {
  attrName: PropTypes.string.isRequired,
  attrInfo: PropTypes.object.isRequired,
};
