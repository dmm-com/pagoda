import { makeStyles } from "@material-ui/core/styles";
import React, { useState } from "react";
import { useAsync } from "react-use";

import Alert from "@material-ui/lab/Alert";
import Button from "@material-ui/core/Button";
import Checkbox from "@material-ui/core/Checkbox";
import FormGroup from "@material-ui/core/FormGroup";
import FormControlLabel from "@material-ui/core/FormControlLabel";
import FormControl from "@material-ui/core/FormControl";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import Modal from "@material-ui/core/Modal";
import TextField from "@material-ui/core/TextField";

import { getWebhooks, setWebhook } from "../../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  modal: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  paper: {
    backgroundColor: theme.palette.background.paper,
    border: "2px solid #000",
    boxShadow: theme.shadows[5],
    padding: theme.spacing(2, 4, 3),
    width: "80%",
  },
}));

export default function WebhookForm({ entityId }) {
  const classes = useStyles();

  const webhooks = useAsync(async () => {
    return getWebhooks(entityId).then((resp) => resp.json());
  });

  console.log(webhooks);

  const [open, setOpen] = React.useState(false);
  const [webhook_headers, setWebhookHeaders] = React.useState(Array());
  const [is_available, setAvailability] = React.useState(false);
  const [webhook_url, setWebhookURL] = React.useState("");
  const [webhook_label, setWebhookLabel] = React.useState("");
  const [alert_msg, setAlertMsg] = React.useState("");

  const handleOpenModal = () => {
    setOpen(true);
    setWebhookURL("");
    setWebhookLabel("");
    setWebhookHeaders(Array());
    setAlertMsg("");
    setAvailability(false);
  };

  const handleCloseModal = () => {
    setOpen(false);
  };

  const handleRegisterWebhook = () => {
    // This parameter is invalid on purpose
    const request_parameter = {
      label: webhook_label,
      webhook_url: webhook_url,
      request_headers: webhook_headers,
      is_enabled: is_available,
    };

    console.log(request_parameter);

    setWebhook(entityId, request_parameter).then((resp) => {
      if (resp.ok) {
        handleCloseModal();
      } else {
        setAlertMsg(resp.statusText);
      }
    });

    registerWebhook(webhooks.concat("test"));
  };

  const handleAddHeaderElem = () => {
    setWebhookHeaders([...webhook_headers, { key: "", value: "" }]);
  };

  const handleDeleteHeaderElem = (e, index) => {
    webhook_headers.splice(index, 1);
    setWebhookHeaders([...webhook_headers]);
  };

  const handleChangeHeaderKey = (e, index) => {
    webhook_headers[index]["key"] = e.target.value;
    setWebhookHeaders([...webhook_headers]);
  };

  const handleChangeHeaderValue = (e, index) => {
    webhook_headers[index]["value"] = e.target.value;
    setWebhookHeaders([...webhook_headers]);
  };

  const handleChangeAvailability = (e) => {
    setAvailability(e.target.checked);
  };

  const handleChangeWebhookURL = (e) => {
    setWebhookURL(e.target.value);
  };

  const handleChangeWebhookLabel = (e) => {
    setWebhookLabel(e.target.value);
  };

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
        {!webhooks.loading &&
          webhooks.value.map((item) => (
            <>
              <ListItem>{item.url}</ListItem>
              <ListItem>{item.label}</ListItem>
              <ListItem>{item.is_enabled}</ListItem>
              <ListItem>{item.is_verified}</ListItem>
            </>
          ))}
      </List>

      <Modal
        aria-labelledby="transition-modal-title"
        aria-describedby="transition-modal-description"
        className={classes.modal}
        open={open}
        onClose={handleCloseModal}
      >
        <div className={classes.paper}>
          <div hidden={alert_msg === ""}>
            <Alert severity="warning">{alert_msg}</Alert>
          </div>

          <h2 id="transition-modal-title">Webhook の登録</h2>
          <form className={classes.root} noValidate autoComplete="off">
            <div>
              <TextField
                id="input-webhoook-url"
                label="Webhook URL"
                variant="outlined"
                onChange={handleChangeWebhookURL}
              />
            </div>

            <div>
              <TextField
                id="input-label"
                label="Label (Optional)"
                variant="outlined"
                onChange={handleChangeWebhookLabel}
              />
            </div>
            <div>
              <FormControl component="fieldset">
                <FormGroup aria-label="position" row>
                  <FormControlLabel
                    value="end"
                    control={
                      <Checkbox
                        color="primary"
                        onChange={handleChangeAvailability}
                      />
                    }
                    label="有効化"
                    labelPlacement="end"
                  />
                </FormGroup>
              </FormControl>
            </div>

            <div>
              <h2>Additional Headers (Optional)</h2>
            </div>

            <div className={classes.webhook_headers_container}>
              {webhook_headers.map((data, index) => (
                <div key={index}>
                  <TextField
                    className={classes.header_key}
                    label="Header Key {index}"
                    variant="outlined"
                    onChange={(e) => handleChangeHeaderKey(e, index)}
                    value={data["key"]}
                  />
                  <TextField
                    className={classes.header_value}
                    label={`Header Value ${index}`}
                    variant="outlined"
                    onChange={(e) => handleChangeHeaderValue(e, index)}
                    value={data["value"]}
                  />
                  <Button
                    variant="contained"
                    color="secondary"
                    onClick={(e) => handleDeleteHeaderElem(e, index)}
                  >
                    -
                  </Button>
                </div>
              ))}
            </div>

            <div>
              ここで入力した情報を、リクエストのヘッダ情報に付加します。必要に応じてご入力ください。
            </div>
            <div>
              <Button
                variant="contained"
                color="primary"
                onClick={handleAddHeaderElem}
              >
                +
              </Button>
            </div>
          </form>

          <Button
            className={classes.button}
            onClick={handleRegisterWebhook}
            type="submit"
            variant="contained"
            color="secondary"
          >
            REGISTER
          </Button>
        </div>
      </Modal>
    </div>
  );
}
