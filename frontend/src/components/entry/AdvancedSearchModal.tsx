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
import React, { Dispatch, FC, useMemo, useState, SetStateAction } from "react";
import { Link } from "react-router-dom";

import { advancedSearchResultPath } from "Routes";

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
  attrNames: string[];
  initialAttrNames: string[];
}

export const AdvancedSearchModal: FC<Props> = ({
  openModal,
  setOpenModal,
  attrNames,
  initialAttrNames,
}) => {
  const classes = useStyles();
  const [selectedAttrNames, setSelectedAttrNames] = useState(initialAttrNames);

  const searchParams = useMemo(() => {
    console.log(
      "[onix/AdvancedSearchModal(00)] selectedAttrNames: ",
      selectedAttrNames
    );
    const params = new URLSearchParams(location.search);

    // ToDo: We have to do work it!!
    /*
    const entityIds = params.getAll("entity").map((id) => Number(id));
    const entryName = params.has("entry_name") ? params.get("entry_name") : "";
    const hasReferral = params.has("has_referral") ? params.get("has_referral") : "";

    entityIds.forEach((e) => {
      params.append("entity", e.toString());
    });
    params.append("has_referral", hasReferral);

    // TODO: The current implementation eliminate current keyword
    params.append(
      "attrinfo",
      JSON.stringify(selectedAttrNames.map((attr) => ({ name: attr })))
    );
    */

    return params;
  }, [selectedAttrNames]);

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
          options={attrNames}
          defaultValue={initialAttrNames}
          onChange={(_, value: Array<string>) => setSelectedAttrNames(value)}
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
            component={Link}
            to={`${advancedSearchResultPath()}?${searchParams}`}
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
