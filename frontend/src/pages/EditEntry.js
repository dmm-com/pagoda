import React, {useEffect, useState} from "react";
import {useParams, Link, useHistory} from "react-router-dom";
import {makeStyles} from "@material-ui/core/styles";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import AironeBreadcrumbs from "../components/AironeBreadcrumbs";
import {createEntry, getEntity, getEntry} from "../utils/AironeAPIClient";
import Button from "@material-ui/core/Button";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
}));

export default function EditEntry(props) {
    const classes = useStyles();
    const history = useHistory();

    const {entityId, entryId} = useParams();
    const [name, setName] = useState('');
    const [attributes, setAttributes] = useState([]);

    useEffect(() => {
        if (entryId !== undefined) {
            getEntry(entityId, entryId)
                .then(data => {
                    setName(data.name);
                    setAttributes(data.attributes);
                });
        }
    }, []);

    const onChangeName = (event) => {
        setName(event.target.value);
    };

    const onChangeAttribute = (event) => {
        attributes[event.target.name] = event.target.value;
        const updated = attributes.map(attribute => {
            if (attribute.name === event.target.name) {
                attribute.value = event.target.value;
            }
            return attribute;
        })
        setAttributes(updated);
    };

    const handleSubmit = (event) => {
        const attrs = attributes.map((attribute) => {
            return {
                id: '4',
                type: '2',
                value: [{'data': attribute.name}],
            };
        });
        createEntry(entityId, name, attrs)
            .then(resp => resp.json())
            .then(_ => history.push(`/new-ui/entities/${entityId}/entries`));

        event.preventDefault();
    };

    return (
        <div>
            <AironeBreadcrumbs>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography component={Link} to='/new-ui/entities'>エンティティ一覧</Typography>
                <Typography component={Link} to={`/new-ui/entities/${entityId}/entries`}>{entityId}</Typography>
                <Typography color="textPrimary">編集</Typography>
            </AironeBreadcrumbs>

            <form onSubmit={handleSubmit}>
                <div className='row'>
                    <div className="col">
                        <div className="float-right">
                            <Button className={classes.button} type="submit" variant="contained"
                                    color="secondary">保存</Button>
                        </div>
                        <Table className="table table-bordered">
                            <TableBody>
                                <TableRow>
                                    <TableCell>エントリ名</TableCell>
                                    <TableCell>
                                        <input type="text" value={name} onChange={onChangeName}/>
                                    </TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>
                    </div>
                </div>

                <Table className="table table-bordered">
                    <TableHead>
                        <TableCell>属性</TableCell>
                        <TableCell>属性値</TableCell>
                    </TableHead>
                    <TableBody>
                        {
                            attributes.map((attribute) =>
                                <TableRow>
                                    <TableCell>{attribute.name}</TableCell>
                                    <TableCell>
                                        <input type="text" name={attribute.name} value={attribute.value}
                                               onChange={onChangeAttribute}/>
                                    </TableCell>
                                </TableRow>
                            )
                        }
                    </TableBody>
                </Table>

                <strong>(*)</strong> は必須項目
            </form>
        </div>
    );
}
