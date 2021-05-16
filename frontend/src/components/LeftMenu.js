import React from "react";
import {makeStyles} from '@material-ui/core/styles';
import {List, ListItem} from "@material-ui/core";
import Box from "@material-ui/core/Box";

const useStyles = makeStyles((theme) => ({
    LeftMenu: {
        backgroundColor: '#d2d4d5',
        height: '100vh',
    },
}));

export default function LeftMenu(props) {
    const classes = useStyles();

    return (
        <Box className={classes.LeftMenu}>
            <List>
                <ListItem>test</ListItem>
            </List>
        </Box>
    );
}
