import {
  Button,
  List,
  ListItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { useHistory } from "react-router-dom";

import { cancelJob, rerunJob } from "../../utils/AironeAPIClient";
import { Confirmable } from "../common/Confirmable";

interface Job {
  id: number;
  operation: string;
  status: number;
  passed_time: string;
  created_at: string;
  note: string;
  target?: {
    name: string;
  };
}

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  jobs: Job[];
}

export const JobList: FC<Props> = ({ jobs }) => {
  const classes = useStyles();
  const history = useHistory();

  const handleRerun = async (jobId: number) => {
    await rerunJob(jobId);
    history.go(0);
  };

  const handleCancel = async (jobId: number) => {
    await cancelJob(jobId);
    history.go(0);
  };

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
            <TableRow key={job.id}>
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
                      onClick={() => handleRerun(job.id)}
                    >
                      Re-run
                    </Button>
                  </ListItem>
                  <ListItem>
                    <Confirmable
                      componentGenerator={(handleOpen) => (
                        <Button
                          variant="contained"
                          color="secondary"
                          className={classes.button}
                          onClick={handleOpen}
                        >
                          Cancel
                        </Button>
                      )}
                      dialogTitle="本当にキャンセルしますか？"
                      onClickYes={() => cancelJob(job.id)}
                    />
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
