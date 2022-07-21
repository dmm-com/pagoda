import {
  Modal,
  Box,
  Autocomplete,
  Checkbox,
  TextField,
  Typography,
  Theme,
  Button,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { Dispatch, FC, SetStateAction } from "react";

const useStyles = makeStyles<Theme>((theme) => ({
  modal: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  paper: {
    backgroundColor: theme.palette.background.paper,
    border: "1px solid #000",
    boxShadow: theme.shadows[5],
    padding: theme.spacing(2, 4, 2),
    width: "50%",
  },
}));

interface Props {
  openModal: boolean;
  setOpenModal: Dispatch<SetStateAction<boolean>>;
}

export const AdvancedSearchModal: FC<Props> = ({ openModal, setOpenModal }) => {
  const classes = useStyles();

  return (
    <Modal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      className={classes.modal}
      open={openModal}
      onClose={() => setOpenModal(false)}
    >
      <Box className={classes.paper}>
        <Typography color="primary">検索属性の再設定</Typography>

        <Autocomplete
          options={["hoge"]}
          //value={selectedAttrs}
          //onChange={(_, value: Array<string>) => setSelectedAttrs(value)}
          renderInput={(params) => (
            <TextField
              {...params}
              variant="outlined"
              placeholder="属性を選択"
            />
          )}
          multiple
          sx={{ width: "100%", margin: "20px 0" }}
        />
        <Box display="flex" justifyContent="center">
          <Box>
            参照エントリも含める
            <Checkbox
              checked
              //onChange={(e) => setHasReferral(e.target.checked)}
            ></Checkbox>
          </Box>
        </Box>
        <Box display="flex" justifyContent="flex-end" my="8px">
          <Button
            variant="contained"
            color="secondary"
            sx={{ mx: "4px" }}
            //disabled={!entries}
            //onClick={handleCopy}
          >
            保存
          </Button>
          <Button
            variant="outlined"
            color="primary"
            sx={{ mx: "4px" }}
            //onClick={handleCancel}
          >
            キャンセル
          </Button>
        </Box>
      </Box>
    </Modal>
  );
};
