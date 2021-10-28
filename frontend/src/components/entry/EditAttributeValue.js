import Card from "@material-ui/core/Card";
import Checkbox from "@material-ui/core/Checkbox";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import PropTypes from "prop-types";
import React from "react";

import { DjangoContext } from "../../utils/DjangoContext";

function ElemString({ attrValue, handleChange }) {
  return (
    <input
      type="text"
      name={attrValue}
      value={attrValue}
      onChange={handleChange}
    />
  );
}

function ElemBool({ attrValue, handleChange }) {
  return <Checkbox checked={attrValue} />;
}

function ElemObject({ attrValue }) {
  //  return <a href={showEntryPath(attrValue.id)}>{attrValue.name}</a>;
  return (
    <Card variant="outlined">
      <List>
        <>
          <ListItem key="1" dense button divider>
            <ListItemIcon>
              <Checkbox edge="start" tabIndex={-1} disableRipple />
            </ListItemIcon>
            <ListItemText primary={attrValue.name} />
          </ListItem>
        </>
      </List>
      <input text="text" placeholder="エントリ名で絞り込む" />
    </Card>
  );
}

function ElemNamedObject({ attrValue }) {
  const key = Object.keys(attrValue)[0];
  return (
    <>
      <input type="text" name={key} value={key} />
      <ElemObject attrValue={attrValue[key]}></ElemObject>
    </>
  );
}

function ElemGroup({ attrValue }) {
  //  return <a href={groupsPath()}>{attrValue.name}</a>;
  return (
    <Card variant="outlined">
      <List>
        <>
          <ListItem key="1" dense button divider>
            <ListItemIcon>
              <Checkbox edge="start" tabIndex={-1} disableRipple />
            </ListItemIcon>
            <ListItemText primary={attrValue.name} />
          </ListItem>
        </>
      </List>
      <input text="text" placeholder="グループ名で絞り込む" />
    </Card>
  );
}

export function EditAttributeValue({
  attrName,
  attrInfo,
  handleChangeAttribute,
}) {
  const djangoContext = DjangoContext.getInstance();

  switch (attrInfo.type) {
    case djangoContext.attrTypeValue.object:
      return <ElemObject attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.boolean:
      return <ElemBool attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.string:
    case djangoContext.attrTypeValue.text:
    case djangoContext.attrTypeValue.date:
      return (
        <ElemString
          attrValue={attrInfo.value}
          handleChange={handleChangeAttribute}
        />
      );

    case djangoContext.attrTypeValue.named_object:
      return <ElemNamedObject attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.array_object:
      return (
        <List>
          {attrInfo.value.map((info, n) => {
            return (
              <ListItem key={n}>
                <ElemObject attrValue={info} />
              </ListItem>
            );
          })}
        </List>
      );

    case djangoContext.attrTypeValue.array_string:
      return (
        <List>
          {attrInfo.value.map((info, n) => {
            return (
              <ListItem key={n}>
                <ElemString attrValue={info} />
              </ListItem>
            );
          })}
        </List>
      );

    case djangoContext.attrTypeValue.array_named_object:
      return (
        <List>
          {attrInfo.value.map((info, n) => {
            return (
              <ListItem key={n}>
                <ElemNamedObject attrValue={info} />
              </ListItem>
            );
          })}
        </List>
      );

    case djangoContext.attrTypeValue.array_group:
      return (
        <List>
          {attrInfo.value.map((info, n) => {
            return (
              <ListItem key={n}>
                <ElemGroup attrValue={info} />
              </ListItem>
            );
          })}
        </List>
      );

    case djangoContext.attrTypeValue.group:
      return <ElemGroup attrValue={attrInfo.value} />;
  }
}

EditAttributeValue.propTypes = {
  attrName: PropTypes.string.isRequired,
  attrInfo: PropTypes.object.isRequired,
};
