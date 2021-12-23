import {
  Box,
  Link,
  List,
  ListItem,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "@mui/material";
import React, { FC } from "react";

interface Props {
  histories: {
    attr_name: string;
    prev: {
      created_user: string;
      created_time: string;
      value: any;
    };
    curr: {
      created_user: string;
      created_time: string;
      value: any;
    };
  }[];
}

export const EntryHistory: FC<Props> = ({ histories }) => {
  return (
    <Table>
      <TableBody>
        {histories.map((history, index) => (
          <TableRow key={index} className="attr_info">
            <TableCell>{history.attr_name}</TableCell>
            <TableCell>
              {history.prev ? (
                <Box className="container">
                  <Box className="row border">
                    <Box className="col-6 border-right">
                      <Box className="container">
                        <Box className="row">
                          <Box className="col-12 border-bottom">
                            <p>変更前</p>
                          </Box>
                          <Box className="col-12 attr_val prev_attr_value">
                            {history.prev.value}
                          </Box>
                        </Box>
                      </Box>
                    </Box>
                    <Box className="col-6">
                      <Box className="container">
                        <Box className="row">
                          <Box className="col-12 border-bottom">
                            <p>変更後</p>
                          </Box>
                          <Box className="col-12 attr_val curr_attr_value">
                            {history.curr.value}
                          </Box>
                        </Box>
                      </Box>
                    </Box>
                  </Box>
                </Box>
              ) : (
                <Box className="container">
                  <Box className="row border">
                    <Box className="col-12 border-bottom">
                      <p>初期値</p>
                    </Box>
                    <Box className="col-12 attr_val">{history.curr.value}</Box>
                  </Box>
                </Box>
              )}
            </TableCell>

            <TableCell>
              <List className="list-group">
                <ListItem className="list-group-item curr_updated_user">
                  {history.curr.created_user}
                </ListItem>
                <ListItem className="list-group-item curr_updated_time">
                  {history.curr.created_time}
                </ListItem>
              </List>
            </TableCell>
            <TableCell>
              <span className="replace_attrv" data-toggle="tooltip">
                {history.prev && (
                  <Link href="#">
                    <img
                      src="/static/images/update.png"
                      data-toggle="modal"
                      data-target="#renew_checkbox"
                      alt="update"
                    />
                  </Link>
                )}
              </span>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
