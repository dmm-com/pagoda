import DeleteIcon from "@mui/icons-material/Delete";
import GroupIcon from "@mui/icons-material/Group";
import {
  Box,
  Button,
  Checkbox,
  Input,
  List,
  ListItemText,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { Link, useHistory } from "react-router-dom";

import { aclPath, entitiesPath } from "../../Routes";
import { createEntity, updateEntity } from "../../utils/AironeAPIClient";

const BaseAttributeTypes = {
  object: 1 << 0,
  string: 1 << 1,
  text: 1 << 2,
  bool: 1 << 3,
  group: 1 << 4,
  date: 1 << 5,
  array: 1 << 10,
  named: 1 << 11,
};

export const AttributeTypes = {
  object: {
    name: "entry",
    type: BaseAttributeTypes.object,
  },
  string: {
    name: "string",
    type: BaseAttributeTypes.string,
  },
  named_object: {
    name: "named_entry",
    type: BaseAttributeTypes.object | BaseAttributeTypes.named,
  },
  array_object: {
    name: "array_entry",
    type: BaseAttributeTypes.object | BaseAttributeTypes.array,
  },
  array_string: {
    name: "array_string",
    type: BaseAttributeTypes.string | BaseAttributeTypes.array,
  },
  array_named_object: {
    name: "array_named_entry",
    type:
      BaseAttributeTypes.object |
      BaseAttributeTypes.named |
      BaseAttributeTypes.array,
  },
  array_group: {
    name: "array_group",
    type: BaseAttributeTypes.group | BaseAttributeTypes.array,
  },
  text: {
    name: "textarea",
    type: BaseAttributeTypes.text,
  },
  boolean: {
    name: "boolean",
    type: BaseAttributeTypes.bool,
  },
  group: {
    name: "group",
    type: BaseAttributeTypes.group,
  },
  date: {
    name: "date",
    type: BaseAttributeTypes.date,
  },
};

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  entity?: {
    id: number;
    name: string;
    note: string;
    isTopLevel: boolean;
    attributes: any[];
  };
  referralEntities?: {
    id: number;
    name: string;
    status: number;
    note: string;
  }[];
}

export const EntityForm: FC<Props> = ({
  entity = {},
  referralEntities = [],
}) => {
  const classes = useStyles();
  const history = useHistory();

  const createMode = entity.id === undefined;
  const [name, setName] = useState(entity.name ? entity.name : "");
  const [note, setNote] = useState(entity.note ? entity.note : "");
  const [isTopLevel, setIsTopLevel] = useState(
    entity.isTopLevel ? entity.isTopLevel : false
  );
  const [attributes, setAttributes] = useState(
    entity.attributes ? entity.attributes : []
  );

  const handleChangeAttributeValue = (index, key, value) => {
    attributes[index][key] = value;
    setAttributes([...attributes]);
  };

  const handleAppendAttribute = () => {
    setAttributes([
      ...attributes,
      {
        name: "",
        type: AttributeTypes.string.type,
        is_mandatory: false,
        is_delete_in_chain: false,
      },
    ]);
  };

  const handleDeleteAttribute = (event, index) => {
    attributes.splice(index, 1);
    setAttributes([...attributes]);
  };

  const handleSubmit = (event) => {
    // Adjusted attributes for the API
    const attrs = attributes.map((attr, index) => {
      return {
        id: attr.id,
        name: attr.name,
        type: String(attr.type),
        row_index: String(index),
        is_mandatory: attr.is_mandatory,
        is_delete_in_chain: attr.is_delete_in_chain,
        ref_ids: attr.referrals.map((r) => r.id),
      };
    });

    if (createMode) {
      createEntity(name, note, isTopLevel, attrs)
        .then((resp) => resp.json())
        .then(() => history.replace(entitiesPath()));
    } else {
      updateEntity(entity.id, name, note, isTopLevel, attrs)
        .then((resp) => resp.json())
        .then(() => history.replace(entitiesPath()));
    }

    event.preventDefault();
  };

  return (
    <form onSubmit={handleSubmit}>
      <Box className="container-fluid">
        <Box className="row">
          <Box className="col">
            <Box className="float-right">
              <Button
                className={classes.button}
                type="submit"
                variant="contained"
                color="secondary"
              >
                保存
              </Button>
            </Box>
            <Table className="table table-bordered">
              <TableBody>
                <TableRow>
                  <TableCell>エンティティ名</TableCell>
                  <TableCell>
                    <Input
                      type="text"
                      name="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>備考</TableCell>
                  <TableCell>
                    <Input
                      type="text"
                      name="note"
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                    />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>サイドバーに表示</TableCell>
                  <TableCell>
                    <Checkbox
                      checked={isTopLevel}
                      onChange={(e) => setIsTopLevel(e.target.checked)}
                    />
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>

            <Table className="table table-bordered">
              <TableHead>
                <TableRow>
                  <TableCell>属性名</TableCell>
                  <TableCell>型</TableCell>
                  <TableCell>オプション</TableCell>
                  <TableCell />
                </TableRow>
              </TableHead>

              <TableBody id="sortdata">
                {attributes.map((attr, index) => (
                  <TableRow key={index} className="attr">
                    <TableCell>
                      <Input
                        type="text"
                        className="attr_name"
                        value={attr.name}
                        onChange={(e) =>
                          handleChangeAttributeValue(
                            index,
                            "name",
                            e.target.value
                          )
                        }
                      />
                    </TableCell>

                    <TableCell>
                      <Box display="flex">
                        <Box minWidth={100} marginX={1}>
                          <Select
                            fullWidth={true}
                            value={attr.type}
                            disabled={!createMode}
                            onChange={(e) =>
                              handleChangeAttributeValue(
                                index,
                                "type",
                                e.target.value
                              )
                            }
                          >
                            {Object.keys(AttributeTypes).map(
                              (typename, index) => (
                                <MenuItem
                                  key={index}
                                  value={AttributeTypes[typename].type}
                                >
                                  {AttributeTypes[typename].name}
                                </MenuItem>
                              )
                            )}
                          </Select>
                        </Box>
                        <Box minWidth={100} marginX={1}>
                          {createMode &&
                            (attr.type & BaseAttributeTypes.object) > 0 && (
                              <>
                                <Typography>参照エントリ: </Typography>
                                {/* TODO multiple */}
                                <Select fullWidth={true}>
                                  {referralEntities.map((e) => (
                                    <MenuItem key={e.id} value={e.id}>
                                      {e.name}
                                    </MenuItem>
                                  ))}
                                </Select>
                              </>
                            )}
                          {!createMode && attr.referrals.length > 0 && (
                            <>
                              <Typography>参照エントリ: </Typography>
                              <List>
                                {attr.referrals.map((r) => (
                                  <ListItemText key={r.id}>
                                    {r.name}
                                  </ListItemText>
                                ))}
                              </List>
                            </>
                          )}
                        </Box>
                      </Box>
                    </TableCell>

                    <TableCell>
                      <Box>
                        <input
                          type="checkbox"
                          checked={attr.is_mandatory}
                          onChange={(e) =>
                            handleChangeAttributeValue(
                              index,
                              "is_mandatory",
                              e.target.checked
                            )
                          }
                        />
                        必須
                      </Box>
                      <Box>
                        <Checkbox
                          checked={attr.is_delete_in_chain}
                          onChange={(e) =>
                            handleChangeAttributeValue(
                              index,
                              "is_delete_in_chain",
                              e.target.checked
                            )
                          }
                        />
                        関連削除
                      </Box>
                    </TableCell>

                    <TableCell>
                      <Box sx={{ flexDirection: "row" }}>
                        <Button
                          variant="contained"
                          color="primary"
                          className={classes.button}
                          startIcon={<GroupIcon />}
                          component={Link}
                          to={aclPath(attr.id)}
                        >
                          ACL
                        </Button>
                        <Button
                          variant="contained"
                          color="secondary"
                          className={classes.button}
                          startIcon={<DeleteIcon />}
                          onClick={(e) => handleDeleteAttribute(e, index)}
                        >
                          削除
                        </Button>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        </Box>

        <Box className="row">
          <Box className="col">
            <Button
              className={classes.button}
              variant="outlined"
              color="primary"
              onClick={handleAppendAttribute}
            >
              属性追加
            </Button>
          </Box>
        </Box>
      </Box>
    </form>
  );
};
