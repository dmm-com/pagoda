import { Box, Button } from "@mui/material";
import { FC } from "react";
import { useNavigate } from "react-router";

import { AttrFilter } from "../../services/entry/AdvancedSearch";

import { AironeModal } from "components/common/AironeModal";

interface Props {
  openModal: boolean;
  handleClose: () => void;
  targetAttrname?: string;
  targetAttrinfo?: AttrFilter;
}

export const AdvancedSearchEditModal: FC<Props> = ({
  openModal,
  handleClose,
  targetAttrname,
  targetAttrinfo,
}) => {
  const navigate = useNavigate();

  const handleSubmit = () => {
    console.log(
      "[onix/handleSubmit(00)] targetAttrname: ",
      targetAttrname,
      " targetAttrinfo: ",
      targetAttrinfo,
    );
    handleClose();
  };

  return (
    <AironeModal
      title={"結合するアイテムの属性名"}
      open={openModal}
      onClose={handleClose}
    >
      <Box display="flex" justifyContent="flex-end" my="8px">
        <Button
          variant="contained"
          color="secondary"
          sx={{ mx: "4px" }}
          onClick={handleSubmit}
        >
          保存
        </Button>
        <Button
          variant="outlined"
          color="primary"
          sx={{ mx: "4px" }}
          onClick={handleClose}
        >
          キャンセル
        </Button>
      </Box>
    </AironeModal>
  );
};
