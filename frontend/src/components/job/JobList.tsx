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
import Button from "@material-ui/core/Button";
import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  jobs: any[];
}

export const JobList: FC<Props> = ({ jobs }) => {
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
                <Typography>{job.target && job.target.name}</Typography>
              </TableCell>
              <TableCell>
                <Typography>{job.operation}</Typography>
              </TableCell>
              <TableCell>
                <Typography>{job.status}</Typography>
              </TableCell>
              <TableCell>
                <Typography>{job.passed_time} s</Typography>
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
};
