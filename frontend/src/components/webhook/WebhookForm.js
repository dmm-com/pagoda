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

  const handleOpenModal = () => {
    setOpen(true);
  }

  const handleCloseModal = () => {
    setOpen(false);
  }

  const handleRegisterWebhook = () => {
    registerWebhook(webhooks.concat('test'));
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
          <div>Webhook URL</div>
          <form className={classes.root} noValidate autoComplete="off">
            <Input defaultValue="" inputProps={{ 'aria-label': 'description' }} />
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
