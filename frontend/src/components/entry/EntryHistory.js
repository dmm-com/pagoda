import {
  Box,
  Link,
  List,
  ListItem,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "@material-ui/core";
import PropTypes from "prop-types";
import React from "react";

export default function EntryHistory({ histories }) {
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
                            <center>変更前</center>
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
                            <center>変更後</center>
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
                      <center>初期値</center>
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
}

EntryHistory.propTypes = {
  histories: PropTypes.arrayOf(
    PropTypes.shape({
      attr_name: PropTypes.string.isRequired,
      prev: PropTypes.shape({
        created_user: PropTypes.string.isRequired,
        created_time: PropTypes.string.isRequired,
        value: PropTypes.any.isRequired,
      }),
      curr: PropTypes.shape({
        created_user: PropTypes.string.isRequired,
        created_time: PropTypes.string.isRequired,
        value: PropTypes.any.isRequired,
      }),
    })
  ).isRequired,
};
