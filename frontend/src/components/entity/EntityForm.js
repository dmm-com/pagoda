import { makeStyles } from "@material-ui/core/styles";
import React, { useRef, useState } from "react";
import Button from "@material-ui/core/Button";
import {
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@material-ui/core";
import { AttributeTypes } from "../../utils/Constants";
import DeleteIcon from "@material-ui/icons/Delete";
import { createEntity } from "../../utils/AironeAPIClient";
import { useHistory } from "react-router-dom";
import PropTypes from "prop-types";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export default function EntityForm({
  initName = "",
  initNote = "",
  initIsTopLevel = false,
  initAttributes = [],
}) {
  const classes = useStyles();
  const history = useHistory();

  const nameRef = useRef(initName);
  const noteRef = useRef(initNote);
  const isTopLevelRef = useRef(initIsTopLevel);
  const [attributes, setAttributes] = useState(initAttributes);

  const handleChangeAttributeValue = (event, index, key) => {
    attributes[index][key] = event.target.value;
    setAttributes([...attributes]);
  };

  const handleAppendAttribute = () => {
    setAttributes([
      ...attributes,
      {
        name: "",
        type: AttributeTypes.string,
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
    const attrs_with_index = attributes.map((attr, index) => {
      attr["row_index"] = String(index);
      attr["type"] = String(attr.type);
      return attr;
    });
    createEntity(name, note, attrs_with_index)
      .then((resp) => resp.json())
      .then((data) => history.push("/new-ui/entities/" + data.entity_id));

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
                    <input type="text" name="name" ref={nameRef} />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>備考</TableCell>
                  <TableCell>
                    <input type="text" name="note" size="50" ref={noteRef} />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>サイドバーに表示</TableCell>
                  <TableCell>
                    <input type="checkbox" ref={isTopLevelRef} />
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
                  <TableRow className="attr" key={index}>
                    <TableCell>
                      <input
                        type="text"
                        className="attr_name"
                        value={attr.name}
                        onChange={(e) =>
                          handleChangeAttributeValue(e, index, "name")
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Select
                        value={attr.type}
                        onChange={(e) =>
                          handleChangeAttributeValue(e, index, "type")
                        }
                      >
                        {Object.keys(AttributeTypes).map((typename) => {
                          return (
                            <MenuItem value={AttributeTypes[typename]}>
                              {typename}
                            </MenuItem>
                          );
                        })}
                      </Select>
                    </TableCell>

                    <TableCell>
                      <div>
                        <input
                          type="checkbox"
                          className="is_mandatory"
                          onChange={(e) =>
                            handleChangeAttributeValue(e, index, "is_mandatory")
                          }
                        />{" "}
                        必須
                      </div>
                      <div>
                        <input
                          type="checkbox"
                          className="is_delete_in_chain"
                          onChange={(e) =>
                            handleChangeAttributeValue(
                              e,
                              index,
                              "is_delete_in_chain"
                            )
                          }
                        />{" "}
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
  initName: PropTypes.string,
  initNote: PropTypes.string,
  initIsTopLevel: PropTypes.bool,
  initAttributes: PropTypes.array,
};
