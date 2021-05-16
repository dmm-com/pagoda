import React from "react";
import {grey} from '@material-ui/core/colors';
import {fade, makeStyles} from '@material-ui/core/styles';
import AccountBox from '@material-ui/icons/AccountBox';
import FindInPageIcon from '@material-ui/icons/FindInPage';
import FormatListBulletedIcon from '@material-ui/icons/FormatListBulleted';
import GroupIcon from '@material-ui/icons/Group';
import PersonIcon from '@material-ui/icons/Person';
import SearchIcon from '@material-ui/icons/Search';
import ViewListIcon from '@material-ui/icons/ViewList';
import AppBar from '@material-ui/core/AppBar';
import Box from "@material-ui/core/Box";
import Button from "@material-ui/core/Button";
import IconButton from '@material-ui/core/IconButton';
import InputBase from '@material-ui/core/InputBase';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';

const useStyles = makeStyles((theme) => ({
    root: {
        flexGrow: 1,
    },
    menu: {
        marginRight: theme.spacing(2),
    },
    title: {
        flexGrow: 1,
    },

    search: {
        position: 'relative',
        borderRadius: theme.shape.borderRadius,
        backgroundColor: fade(theme.palette.common.white, 0.15),
        '&:hover': {
            backgroundColor: fade(theme.palette.common.white, 0.25),
        },
        marginRight: theme.spacing(2),
        marginLeft: 0,
        width: '100%',
        [theme.breakpoints.up('sm')]: {
            marginLeft: theme.spacing(3),
            width: 'auto',
        },
    },
    searchIcon: {
        padding: theme.spacing(0, 2),
        height: '100%',
        position: 'absolute',
        pointerEvents: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
    },
    inputRoot: {
        color: 'inherit',
    },
    inputInput: {
        padding: theme.spacing(1, 1, 1, 0),
        // vertical padding + font size from searchIcon
        paddingLeft: `calc(1em + ${theme.spacing(4)}px)`,
        transition: theme.transitions.create('width'),
        width: '100%',
        [theme.breakpoints.up('md')]: {
            width: '20ch',
        },
    },
}));

export default function Header(props) {
    const classes = useStyles();

    return (
        <div className={classes.root}>
            <AppBar position="static">
                <Toolbar>
                    <Typography variant="h6" className={classes.title}>AirOne(New UI)</Typography>
                    <Tabs
                        variant="scrollable"
                        scrollButtons="on"
                        indicatorColor="primary"
                        textColor="primary"
                        aria-label="scrollable force tabs example"
                    >
                        <Tab label="エンティティ・エントリ一覧" icon={<ViewListIcon/>} style={{color: grey[50]}}/>
                        <Tab label="高度な検索" icon={<FindInPageIcon/>} style={{color: grey[50]}}/>
                        <Tab label="ユーザ管理" icon={<PersonIcon/>} style={{color: grey[50]}}/>
                        <Tab label="グループ管理" icon={<GroupIcon/>} style={{color: grey[50]}}/>
                    </Tabs>
                    <Box className={classes.menu}>
                        <IconButton style={{color: grey[50]}}>
                            <AccountBox/>
                        </IconButton>
                        <IconButton style={{color: grey[50]}}>
                            <FormatListBulletedIcon/>
                        </IconButton>
                    </Box>
                    <div className={classes.search}>
                        <div className={classes.searchIcon}>
                            <SearchIcon/>
                        </div>
                        <InputBase
                            placeholder="Search…"
                            classes={{
                                root: classes.inputRoot,
                                input: classes.inputInput,
                            }}
                            inputProps={{'aria-label': 'search'}}
                        />
                        <Button variant="contained">検索</Button>
                    </div>
                </Toolbar>
            </AppBar>
        </div>
    );
}
