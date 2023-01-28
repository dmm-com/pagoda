import {
  Box,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import React, { FC, useEffect } from "react";

import { DjangoContext } from "utils/DjangoContext";

interface AclInfo {
  isPublic: boolean;
  defaultPermission: number;
  permissions: object;
}

interface Props {
  aclInfo: AclInfo;
  setACLInfo: (aclInfo: AclInfo) => void;
  setSubmittable: (isSubmittable: boolean) => void;
}

export const ACLForm: FC<Props> = ({ setSubmittable, aclInfo, setACLInfo }) => {
  const djangoContext = DjangoContext.getInstance();

  const checkSubmittable = () => {
    if (aclInfo.isPublic) {
      return true;
    }
    if (aclInfo.defaultPermission & (djangoContext?.aclTypes.full.value ?? 0)) {
      return true;
    }
    return Object.values(aclInfo.permissions).some(
      (permission) =>
        permission.current_permission &
        (djangoContext?.aclTypes.full.value ?? 0)
    );
  };

  useEffect(() => {
    setSubmittable(checkSubmittable());
  });

  return (
    <Box>
      <Table className="table table-bordered">
        <TableHead>
          <TableRow sx={{ backgroundColor: "#455A64" }}>
            <TableCell sx={{ color: "#FFFFFF" }}>項目</TableCell>
            <TableCell sx={{ color: "#FFFFFF" }}>内容</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>公開設定</TableCell>
            <TableCell>
              {/* TODO fix width */}
              <Select
                fullWidth={true}
                value={aclInfo.isPublic ? 1 : 0}
                onChange={(e) =>
                  setACLInfo({
                    ...aclInfo,
                    isPublic: e.target.value === 1,
                  })
                }
              >
                <MenuItem value={1}>公開</MenuItem>
                <MenuItem value={0}>限定公開</MenuItem>
              </Select>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>

      <Box>
        {!aclInfo.isPublic && (
          <>
            <Box my="32px">
              <Typography variant="h4" align="center">
                公開制限設定
              </Typography>
            </Box>

            <Table className="table table-bordered">
              <TableHead>
                <TableRow sx={{ backgroundColor: "#455A64" }}>
                  <TableCell sx={{ color: "#FFFFFF" }}>ロール</TableCell>
                  <TableCell sx={{ color: "#FFFFFF" }}>備考</TableCell>
                  <TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>全員</TableCell>
                  <TableCell />
                  <TableCell>
                    <Select
                      fullWidth={true}
                      value={aclInfo.defaultPermission}
                      onChange={(e) =>
                        setACLInfo({
                          ...aclInfo,
                          defaultPermission: Number(e.target.value),
                        })
                      }
                    >
                      {Object.keys(djangoContext?.aclTypes ?? {}).map(
                        (key, index) => (
                          <MenuItem
                            key={index}
                            value={djangoContext?.aclTypes[key].value}
                          >
                            {djangoContext?.aclTypes[key].name}
                          </MenuItem>
                        )
                      )}
                    </Select>
                  </TableCell>
                </TableRow>
                {Object.keys(aclInfo.permissions).map((key, index) => (
                  <TableRow key={index}>
                    <TableCell>{aclInfo.permissions[key].name}</TableCell>
                    <TableCell>
                      {aclInfo.permissions[key].description}
                    </TableCell>
                    <TableCell>
                      <Select
                        fullWidth={true}
                        value={aclInfo.permissions[key].current_permission}
                        onChange={(e) =>
                          setACLInfo({
                            ...aclInfo,
                            permissions: {
                              ...aclInfo.permissions,
                              [key]: {
                                ...aclInfo.permissions[key],
                                current_permission: e.target.value,
                              },
                            },
                          })
                        }
                      >
                        <MenuItem value={0}>(未設定)</MenuItem>
                        {Object.keys(djangoContext?.aclTypes ?? {}).map(
                          (key, index) => (
                            <MenuItem
                              key={index}
                              value={djangoContext?.aclTypes[key].value}
                            >
                              {djangoContext?.aclTypes[key].name}
                            </MenuItem>
                          )
                        )}
                      </Select>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}
      </Box>
    </Box>
  );
};
