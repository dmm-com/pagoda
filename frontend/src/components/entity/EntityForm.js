import { makeStyles } from "@material-ui/core/styles";
import React, { useState } from "react";
import Button from "@material-ui/core/Button";
import {
  List,
  ListItemText,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@material-ui/core";
import DeleteIcon from "@material-ui/icons/Delete";
import { createEntity, updateEntity } from "../../utils/AironeAPIClient";
import { useHistory } from "react-router-dom";
import PropTypes from "prop-types";
import Box from "@material-ui/core/Box";
import Typography from "@material-ui/core/Typography";

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

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function EntityForm({ entity = {}, referralEntities = [] }) {
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
        .then(() => history.replace("/new-ui/entities"));
    } else {
      updateEntity(entity.id, name, note, isTopLevel, attrs)
        .then((resp) => resp.json())
        .then(() => history.replace("/new-ui/entities"));
    }

    event.preventDefault();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="container-fluid">
        <div className="row">
          <div className="col">
            <div className="float-right">
              <Button
                className={classes.button}
                type="submit"
                variant="contained"
                color="secondary"
              >
                保存
              </Button>
            </div>
            <Table className="table table-bordered">
              <TableBody>
                <TableRow>
                  <TableCell>エンティティ名</TableCell>
                  <TableCell>
                    <input
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
                    <input
                      type="text"
                      name="note"
                      size="50"
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                    />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>サイドバーに表示</TableCell>
                  <TableCell>
                    <input
                      type="checkbox"
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
                  <TableRow className="attr" key={`attr-${index}`}>
                    <TableCell>
                      <input
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
                      <div>
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
                      </div>
                      <div>
                        <input
                          type="checkbox"
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
                      </div>
                    </TableCell>

                    <TableCell>
                      <Button
                        variant="contained"
                        color="secondary"
                        className={classes.button}
                        startIcon={<DeleteIcon />}
                        onClick={(e) => handleDeleteAttribute(e, index)}
                      >
                        削除
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>

        <div className="row">
          <div className="col">
            <Button
              className={classes.button}
              variant="outlined"
              color="primary"
              onClick={handleAppendAttribute}
            >
              属性追加
            </Button>
          </div>
        </div>
      </div>
    </form>
  );
}

EntityForm.propTypes = {
  entity: PropTypes.exact({
    id: PropTypes.string,
    name: PropTypes.string,
    note: PropTypes.string,
    isTopLevel: PropTypes.bool,
    attributes: PropTypes.array,
  }),
  referralEntities: PropTypes.arrayOf(
    PropTypes.exact({
      id: PropTypes.number,
      name: PropTypes.string,
      status: PropTypes.number,
      note: PropTypes.string,
    })
  ),
};
