import {
  List,
  ListItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";
import Button from "@material-ui/core/Button";
import { Link } from "react-router-dom";
import React from "react";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
}));

export default function JobList({ jobs }) {
  const classes = useStyles();

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>
              <Typography>対象エントリ</Typography>
            </TableCell>
            <TableCell>
              <Typography>操作</Typography>
            </TableCell>
            <TableCell>
              <Typography>状況</Typography>
            </TableCell>
            <TableCell>
              <Typography>実行時間</Typography>
            </TableCell>
            <TableCell>
              <Typography>実行日時</Typography>
            </TableCell>
            <TableCell align="right">
              <Typography>備考</Typography>
            </TableCell>
            <TableCell align="right" />
          </TableRow>
        </TableHead>
        <TableBody>
          {jobs.map((job) => (
            <TableRow>
              <TableCell>
                <Typography>{job.entry}</Typography>
              </TableCell>
              <TableCell>
                <Typography>{job.operation}</Typography>
              </TableCell>
              <TableCell>
                <Typography>{job.status}</Typography>
              </TableCell>
              <TableCell>
                <Typography>{job.duration}</Typography>
              </TableCell>
              <TableCell>
                <Typography>{job.created_at}</Typography>
              </TableCell>
              <TableCell align="right">
                <Typography>{job.note}</Typography>
              </TableCell>
              <TableCell align="right">
                <List>
                  <ListItem>
                    <Button
                      variant="contained"
                      color="primary"
                      className={classes.button}
                      component={Link}
                      to={`/jobs/${job.id}/rerun`}
                    >
                      Re-run
                    </Button>
                  </ListItem>
                  <ListItem>
                    <Button
                      variant="contained"
                      color="secondary"
                      className={classes.button}
                      component={Link}
                      to={`/jobs/${job.id}/cancel`}
                    >
                      Cancel
                    </Button>
                  </ListItem>
                </List>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
