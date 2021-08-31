import { makeStyles } from "@material-ui/core/styles";
import React, { useState } from "react";
import Button from "@material-ui/core/Button";
import PropTypes from "prop-types";
import Modal from '@material-ui/core/Modal';
import Backdrop from '@material-ui/core/Backdrop';
import Fade from '@material-ui/core/Fade';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import Input from '@material-ui/core/Input';
import TextField from '@material-ui/core/TextField';


const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  modal: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  paper: {
    backgroundColor: theme.palette.background.paper,
    border: '2px solid #000',
    boxShadow: theme.shadows[5],
    padding: theme.spacing(2, 4, 3),
    width: '80%',
  },
}));

export default function WebhookForm({
}) {
  const classes = useStyles();

  const [open, setOpen] = React.useState(false);
  const [webhooks, registerWebhook] = React.useState(['hoge', 'fuga']);
  const [headers, setHeaders] = React.useState([])

  const handleOpenModal = () => {
    setOpen(true);
  }

  const handleCloseModal = () => {
    setOpen(false);
  }

  const handleRegisterWebhook = () => {
    registerWebhook(webhooks.concat('test'));
  }

  const handleAddHeaderElem = () => {
    setHeaders([...headers, {}])
  }

  return (
    <div>
      <Button
        className={classes.button}
        onClick={handleOpenModal}
        type="submit"
        variant="contained"
        color="secondary"
      >
        Add Webhook
      </Button>

      <List>
        {
          webhooks.map(item => (
            <ListItem>
              { item }
            </ListItem>
          ))
        }
      </List>

      <Modal
        aria-labelledby="transition-modal-title"
        aria-describedby="transition-modal-description"
        className={classes.modal}
        open={open}
        onClose={handleCloseModal}
      >
        <div className={classes.paper}>
          <h2 id="transition-modal-title">Webhook の登録</h2>
          <form className={classes.root} noValidate autoComplete="off">
            <div>
              <TextField
                id="input-webhoook-url"
                label="Webhook URL"
                variant="outlined"
              />
            </div>

            <div>
              <TextField
                id="input-label"
                label="Label (Optional)"
                variant="outlined"
              />
            </div>

            <div>
              <h2>Additional Headers (Optional)</h2>
            </div>

            <div className={classes.headers_container}>
              {headers.map((data) => (
                <div>
                  <TextField className={classes.header_key} label="Header Key" variant='outlined'/>
                  <TextField className={classes.header_value} label="Header Value" variant="outlined" />
                  <Button variant="contained" color="secondary">-</Button>
                </div>
              ))}
            </div>

            <div>
              ここで入力した情報を、リクエストのヘッダ情報に付加します。必要に応じてご入力ください。
            </div>
            <div>
              <Button variant="contained" color="primary" onClick={handleAddHeaderElem}>+</Button>
            </div>
          </form>

          <Button
            className={classes.button}
            onClick={handleRegisterWebhook}
            type="submit"
            variant="contained"
            color="secondary"
          >
            Add Webhook
          </Button>
        </div>

      </Modal>
    </div>
  );
}
