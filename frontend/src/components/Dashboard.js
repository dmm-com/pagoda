import React from "react";
import Box from "@material-ui/core/Box";
import Breadcrumbs from "@material-ui/core/Breadcrumbs";
import Button from "@material-ui/core/Button";
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';

export default function Dashboard(props) {
    return (
        <Box>
            <Breadcrumbs aria-label="breadcrumb">
                <Typography color="textPrimary">Top</Typography>
            </Breadcrumbs>

            <Typography>まだないよ</Typography>
        </Box>
    );
}
