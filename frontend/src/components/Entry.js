import React from "react";
import Button from "@material-ui/core/Button";
import {useParams, Link} from "react-router-dom";
import {makeStyles} from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
}));

export default function Entry(props) {
    const classes = useStyles();
    let {entityId} = useParams();

    return (
        <div>
            <div className="row">
                <div className="col">
                    <div className="float-left">
                        <Button
                            variant="contained"
                            color="primary"
                            className={classes.button}
                            component={Link}
                            to={`/entry/create/${entityId}`}>
                            エントリ作成
                        </Button>
                        <Button
                            variant="contained"
                            className={classes.button}
                            component={Link}
                            to={`/entity/edit/${entityId}`}>
                            エンティティ編集
                        </Button>
                        <Button
                            variant="contained"
                            className={classes.button}
                            component={Link}
                            to={`/acl/${entityId}`}>
                            エンティティの ACL
                        </Button>
                        <Button
                            variant="contained"
                            color="secondary"
                            className={classes.button}>
                            エクスポート
                        </Button>
                        <Button
                            variant="contained"
                            color="secondary"
                            className={classes.button}
                            component={Link}
                            to={`/entry/import/${entityId}`}>
                            インポート
                        </Button>
                        <Button
                            variant="contained"
                            className={classes.button}>
                            CSV で出力
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
