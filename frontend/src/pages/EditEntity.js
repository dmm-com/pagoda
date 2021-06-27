import React, {useEffect, useState} from "react";
import {makeStyles} from "@material-ui/core/styles";
import {MenuItem, Select, Table, TableBody, TableCell, TableFooter, TableHead, TableRow} from "@material-ui/core";
import Button from "@material-ui/core/Button";
import {Link, useHistory, useParams} from "react-router-dom";
import DeleteIcon from "@material-ui/icons/Delete";
import {createEntity, getEntity} from "../utils/AironeAPIClient";
import {AttributeTypes} from "../utils/Constants";
import AironeBreadcrumbs from "../components/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
}));

export default function EditEntity(props) {
    const classes = useStyles();
    const history = useHistory();
    const {entityId} = useParams();

    const [name, setName] = useState("");
    const [note, setNote] = useState("");
    const [isTopLevel, setIsTopLevel] = useState(false);
    const [attributes, setAttributes] = useState([]);

    useEffect(() => {
        if (entityId !== undefined) {
            getEntity(entityId)
                .then(data => {
                    setName(data.name);
                    setNote(data.note);
                    setAttributes(data.attributes);
                });
        }
    }, []);

    const onChangeName = (event) => {
        setName(event.target.value);
    };

    const onChangeNote = (event) => {
        setNote(event.target.value);
    };

    const onChangeIsTopLevel = (event) => {
        setIsTopLevel(event.target.value);
    };

    const onChangeAttributeValue = (event, index, key) => {
        attributes[index][key] = event.target.value;
        setAttributes([...attributes]);
    };

    const onSubmit = (event) => {
        const attrs_with_index = attributes.map((attr, index) => {
            attr['row_index'] = String(index);
            attr['type'] = String(attr.type);
            return attr;
        });
        createEntity(name, note, attrs_with_index)
            .then(resp => resp.json())
            .then(data => history.push('/new-ui/entities/' + data.entity_id));

        event.preventDefault();
    };

    const appendAttribute = (event) => {
        setAttributes([...attributes, {
            name: "",
            type: AttributeTypes.string,
            is_mandatory: false,
            is_delete_in_chain: false
        }]);
    };

    const deleteAttribute = (event, index) => {
        attributes.splice(index, 1);
        setAttributes([...attributes]);
    };

    return (
        <div>
            <AironeBreadcrumbs>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography component={Link} to={`/new-ui/entities`}>エンティティ一覧</Typography>
                <Typography color="textPrimary">エンティティ編集</Typography>
            </AironeBreadcrumbs>

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
                                        <TableCell><input type="checkbox" value={isTopLevel} onChange={onChangeIsTopLevel}/></TableCell>
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
                                                        <Select value={attr.type}
                                                                onChange={(e) => onChangeAttributeValue(e, index, "type")}>
                                                            {
                                                                Object.keys(AttributeTypes).map(typename => {
                                                                    return <MenuItem
                                                                        value={AttributeTypes[typename]}>{typename}</MenuItem>;
                                                                })
                                                            }
                                                        </Select>
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
                            <Button className={classes.button} variant="outlined"
                                    color="primary" onClick={appendAttribute}>属性追加</Button>
                        </div>
                    </div>
                </div>
            </form>
        </div>
    );
}