import Button from "@material-ui/core/Button";
import React from "react";
import {makeStyles} from "@material-ui/core/styles";
import {Link} from "react-router-dom";
import {Breadcrumbs} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import {grey} from "@material-ui/core/colors";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
    links: {
        display: "flex",
        justifyContent: "center",
    },
    breadcrumbs: {
        padding: theme.spacing(1),
        marginBottom: theme.spacing(1),
        backgroundColor: grey[300],
    },
}));

export default function Dashboard(props) {
    const classes = useStyles();

    return (
        <div>
            <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
                <Typography color="textPrimary">Top</Typography>
            </Breadcrumbs>

            <div className={classes.links}>
                <Button
                    className={classes.button}
                    variant="contained"
                    color="primary"
                    component={Link}
                    to={`/new-ui/entities`}
                >
                    エンティティ・エントリ一覧 &#x000bb;
                </Button>

                <Button
                    className={classes.button}
                    variant="contained"
                    color="primary"
                    component={Link}
                    to={`/new-ui/advanced_search`}
                >
                    高度な検索 &#x000bb;
                </Button>

                <Button
                    className={classes.button}
                    variant="contained"
                    color="primary"
                    component={Link}
                    to={`/new-ui/user`}
                >
                    ユーザ管理 &#x000bb;
                </Button>

                <Button
                    className={classes.button}
                    variant="contained"
                    color="primary"
                    component={Link}
                    to={`/new-ui/group`}
                >
                    グループ管理 &#x000bb;
                </Button>
            </div>
        </div>
    );
}
