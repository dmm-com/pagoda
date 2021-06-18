import React, {useEffect, useState} from "react";
import {makeStyles} from "@material-ui/core/styles";
import {Table, TableBody, TableCell, TableFooter, TableHead, TableRow} from "@material-ui/core";
import Button from "@material-ui/core/Button";
import GroupIcon from "@material-ui/icons/Group";
import {Link} from "react-router-dom";
import DeleteIcon from "@material-ui/icons/Delete";
import {createEntity} from "../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
}));

export default function EditEntity(props) {
    const classes = useStyles();
    const [name, setName] = useState("");
    const [note, setNote] = useState("");
    const [attributes, setAttributes] = useState([]);

    useEffect(() => {
        // TODO get entity, then fill entry
        setName("");
        setNote("");
        setAttributes([]);
    }, []);

    const onChangeName = (event) => {
        setName(event.target.value);
    };

    const onChangeNote = (event) => {
        setNote(event.target.value);
    };

    const onChangeAttributeValue = (event, index, key) => {
        attributes[index][key] = event.target.value;
        setAttributes([...attributes]);
    };

    const onSubmit = (event) => {
        const attrs_with_index = attributes.map((attr, index) => {
            attr['row_index'] = String(index);
            return attr;
        });
        createEntity(name, note, attrs_with_index)
            .then(resp => console.log(resp));

        event.preventDefault();
    };

    const appendAttribute = (event) => {
        setAttributes([...attributes, {name: "", type: '2', is_mandatory: false, is_delete_in_chain: false}]);
    };

    const deleteAttribute = (event, index) => {
        attributes.splice(index, 1);
        setAttributes([...attributes]);
    };

    return (
        <form onSubmit={onSubmit}>
            <div className="container-fluid">
                <div className="row">
                    <div className="col">
                        <div className="float-right">
                            <Button className={classes.button} type="submit" variant="contained"
                                    color="secondary">保存</Button>
                        </div>
                        <Table className="table table-bordered">
                            <TableBody>
                                <TableRow>
                                    <TableCell>エンティティ名</TableCell>
                                    <TableCell><input type="text" name="name" value={name}
                                                      onChange={onChangeName}/></TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell>備考</TableCell>
                                    <TableCell><input type="text" name="note" size="50"
                                                      value={note} onChange={onChangeNote}/></TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell>サイドバーに表示</TableCell>
                                    <TableCell><input type="checkbox" name="is_toplevel"/></TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>

                        <Table className="table table-bordered">
                            <TableHead>
                                <TableRow>
                                    <TableCell>属性名</TableCell>
                                    <TableCell>型</TableCell>
                                    <TableCell>オプション</TableCell>
                                    <TableCell/>
                                </TableRow>
                            </TableHead>

                            <TableBody id='sortdata'>
                                {
                                    attributes.map((attr, index) => {
                                        return (
                                            <TableRow className="attr">
                                                <TableCell>
                                                    <input type="text" className="attr_name" value={attr.name}
                                                           onChange={(e) => onChangeAttributeValue(e, index, "name")}/>
                                                </TableCell>
                                                <TableCell>
                                                    <div className='row'>
                                                        型選択あとでやる
                                                    </div>
                                                </TableCell>

                                                <TableCell>
                                                    <div>
                                                        <input type="checkbox" className="is_mandatory"
                                                               onChange={(e) => onChangeAttributeValue(e, index, "is_mandatory")}/> 必須
                                                    </div>
                                                    <div>
                                                        <input type="checkbox" className="is_delete_in_chain"
                                                               onChange={(e) => onChangeAttributeValue(e, index, "is_delete_in_chain")}/> 関連削除
                                                    </div>
                                                </TableCell>

                                                <TableCell>
                                                    <Button
                                                        variant="contained"
                                                        color="secondary"
                                                        className={classes.button}
                                                        startIcon={<DeleteIcon/>}
                                                        onClick={(e) => deleteAttribute(e, index)}>
                                                        削除
                                                    </Button>
                                                </TableCell>
                                            </TableRow>)
                                    })
                                }
                            </TableBody>
                        </Table>
                    </div>
                </div>

                <div className="row">
                    <div className="col">
                        <button type="button" className="btn btn-primary" name="add_attr"
                                onClick={appendAttribute}>属性追加
                        </button>
                    </div>
                </div>
            </div>
        </form>
    );
}