import Button from "@material-ui/core/Button";
import React from "react";
import {makeStyles} from "@material-ui/core/styles";
import {Link} from "react-router-dom";
import Typography from "@material-ui/core/Typography";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
    links: {
        display: "flex",
        justifyContent: "center",
    },
}));

export default function Dashboard({}) {
    const classes = useStyles();

    return (
        <div>
            <AironeBreadcrumbs>
                <Typography color="textPrimary">Top</Typography>
            </AironeBreadcrumbs>

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
                    to={`/new-ui/users`}
                >
                    ユーザ管理 &#x000bb;
                </Button>

                <Button
                    className={classes.button}
                    variant="contained"
                    color="primary"
                    component={Link}
                    to={`/new-ui/groups`}
                >
                    グループ管理 &#x000bb;
                </Button>
            </div>
        </div>
    );
}
