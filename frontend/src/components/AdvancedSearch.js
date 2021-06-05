import {makeStyles} from "@material-ui/core/styles";
import {grey} from "@material-ui/core/colors";
import React, {useEffect, useState} from "react";
import {Breadcrumbs, Select} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import {Link} from "react-router-dom";
import Button from "@material-ui/core/Button";
import Grid from "@material-ui/core/Grid";

const useStyles = makeStyles((theme) => ({
    breadcrumbs: {
        padding: theme.spacing(1),
        marginBottom: theme.spacing(1),
        backgroundColor: grey[300],
    },
}));

export default function AdvancedSearch(props) {
    const classes = useStyles();
    const [entities, setEntities] = useState([]);

    useEffect(() => {
        setEntities([
            {
                id: 1,
                name: 'entity1',
                attributes: [
                    {
                        id: 1,
                        name: "attr1",
                    },
                    {
                        id: 2,
                        name: "attr2",
                    },
                ]
            },
        ])
    }, []);

    return (
        <div className="container-fluid">
            <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
                <Typography component={Link} to='/new-ui/'>Top</Typography>
                <Typography color="textPrimary">高度な検索</Typography>
            </Breadcrumbs>

            <Typography variant="h5">検索条件:</Typography>

            <div className="row">
                <Typography>検索するエンティティ</Typography>
                <Select
                    multiple
                    native
                    variant="outlined"
                >
                    {entities.map((entity) => (
                        <option key="entities" value={entity.id}>
                            {entity.name}
                        </option>
                    ))}
                </Select>
            </div>

            <div className="row">
                <Typography>検索する属性</Typography>
                <Select
                    multiple
                    native
                    variant="outlined"
                >
                    {entities.map((entity) => {
                        return (
                            <optgroup label={entity.name}>
                                {
                                    entity.attributes.map((attribute) => (
                                        <option key="attribute" value={attribute.id}>
                                            {attribute.name}
                                        </option>
                                    ))
                                }
                            </optgroup>
                        );
                    })}
                </Select>
            </div>

            <Grid container justify="flex-end">
                <Grid item xs={1}>
                    <Button
                        variant="contained"
                        component={Link}
                        to={`/new-ui/search`}
                    >
                        検索
                    </Button>
                </Grid>
            </Grid>
        </div>
    );
}
