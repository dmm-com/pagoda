import { Entity } from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Autocomplete,
  Box,
  Checkbox,
  IconButton,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC } from "react";
import { Control, Controller, useFieldArray, useWatch } from "react-hook-form";

import { Schema } from "./EntityFormSchema";

import { ReferralsAutocomplete } from "components/entry/entryForm/ReferralsAutocomplete";
import { BaseAttributeTypes } from "services/Constants";

// Attribute types supported in isolation conditions (same as trigger conditions)
const ISOLATION_SUPPORTED_TYPES = [
  BaseAttributeTypes.string,
  BaseAttributeTypes.string | BaseAttributeTypes.array,
  BaseAttributeTypes.bool,
  BaseAttributeTypes.object,
  BaseAttributeTypes.object | BaseAttributeTypes.array,
  BaseAttributeTypes.object | BaseAttributeTypes.named,
  BaseAttributeTypes.object |
    BaseAttributeTypes.named |
    BaseAttributeTypes.array,
];

const HeaderTableRow = styled(TableRow)(() => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(() => ({
  color: "#FFFFFF",
  boxSizing: "border-box",
}));

const StyledTableRow = styled(TableRow)(() => ({
  "& td": {
    padding: "8px",
    verticalAlign: "top",
  },
}));

interface Props {
  control: Control<Schema>;
  referralEntities: Entity[];
}

interface ConditionValueProps {
  ruleIndex: number;
  condIndex: number;
  attrType: number;
  attrId: number | undefined;
  control: Control<Schema>;
}

const IsolationConditionValue: FC<ConditionValueProps> = ({
  ruleIndex,
  condIndex,
  attrType,
  attrId,
  control,
}) => {
  const isObject = (attrType & BaseAttributeTypes.object) !== 0;
  const isNamed = isObject && (attrType & BaseAttributeTypes.named) !== 0;
  const isBool = (attrType & BaseAttributeTypes.bool) !== 0;

  if (isBool) {
    return (
      <Controller
        name={`isolationRules.${ruleIndex}.conditions.${condIndex}.boolCond`}
        control={control}
        render={({ field }) => (
          <Checkbox
            checked={field.value}
            onChange={(e) => field.onChange(e.target.checked)}
          />
        )}
      />
    );
  }

  if (isNamed) {
    return (
      <Box display="flex" gap={1} alignItems="flex-end">
        <Controller
          name={`isolationRules.${ruleIndex}.conditions.${condIndex}.strCond`}
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              value={field.value ?? ""}
              variant="standard"
              placeholder="名前"
              size="small"
            />
          )}
        />
        {attrId != null && (
          <Box flexGrow={1}>
            <Controller
              name={`isolationRules.${ruleIndex}.conditions.${condIndex}.refCond`}
              control={control}
              render={({ field }) => (
                <ReferralsAutocomplete
                  attrId={attrId}
                  value={field.value}
                  handleChange={(v) => field.onChange(v)}
                  multiple={false}
                />
              )}
            />
          </Box>
        )}
      </Box>
    );
  }

  if (isObject) {
    if (attrId == null) return null;
    return (
      <Controller
        name={`isolationRules.${ruleIndex}.conditions.${condIndex}.refCond`}
        control={control}
        render={({ field }) => (
          <ReferralsAutocomplete
            attrId={attrId}
            value={field.value}
            handleChange={(v) => field.onChange(v)}
            multiple={false}
          />
        )}
      />
    );
  }

  // string / text / array_string
  return (
    <Controller
      name={`isolationRules.${ruleIndex}.conditions.${condIndex}.strCond`}
      control={control}
      render={({ field }) => (
        <TextField
          {...field}
          value={field.value ?? ""}
          variant="standard"
          fullWidth
          size="small"
        />
      )}
    />
  );
};

interface ConditionsCellProps {
  ruleIndex: number;
  control: Control<Schema>;
  savedAttrs: Array<{ id?: number; name: string; type: number }>;
}

const IsolationConditionsCell: FC<ConditionsCellProps> = ({
  ruleIndex,
  control,
  savedAttrs,
}) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: `isolationRules.${ruleIndex}.conditions`,
    keyName: "key",
  });

  const emptyCondition = () => ({
    id: undefined,
    attr: { id: 0, name: "", type: 0 },
    strCond: null,
    refCond: null,
    boolCond: false,
    isUnmatch: false,
  });

  return (
    <Box>
      {fields.map((condField, condIndex) => (
        <IsolationConditionRow
          key={condField.key}
          ruleIndex={ruleIndex}
          condIndex={condIndex}
          control={control}
          savedAttrs={savedAttrs}
          onRemove={() => remove(condIndex)}
          onAddAfter={() => insert(condIndex + 1, emptyCondition())}
        />
      ))}
      {fields.length === 0 && (
        <IconButton size="small" onClick={() => insert(0, emptyCondition())}>
          <AddIcon />
        </IconButton>
      )}
    </Box>
  );
};

interface ConditionRowProps {
  ruleIndex: number;
  condIndex: number;
  control: Control<Schema>;
  savedAttrs: Array<{ id?: number; name: string; type: number }>;
  onRemove: () => void;
  onAddAfter: () => void;
}

const IsolationConditionRow: FC<ConditionRowProps> = ({
  ruleIndex,
  condIndex,
  control,
  savedAttrs,
  onRemove,
  onAddAfter,
}) => {
  const attrId = useWatch({
    control,
    name: `isolationRules.${ruleIndex}.conditions.${condIndex}.attr.id`,
  });
  const selectedAttr = savedAttrs.find((a) => a.id === attrId);

  return (
    <Box display="flex" gap={1} alignItems="center" mb={0.5}>
      <Controller
        name={`isolationRules.${ruleIndex}.conditions.${condIndex}.attr.id`}
        control={control}
        render={({ field }) => (
          <Select
            value={field.value || 0}
            onChange={(e) => {
              const found = savedAttrs.find(
                (a) => a.id === Number(e.target.value),
              );
              field.onChange(Number(e.target.value));
              // Reset value fields when attr changes
              if (found) {
                // type change is handled by watching attrId
              }
            }}
            size="small"
            sx={{ minWidth: 200 }}
          >
            <MenuItem value={0} disabled>
              属性を選択
            </MenuItem>
            {savedAttrs
              .filter((a) => ISOLATION_SUPPORTED_TYPES.includes(a.type))
              .map((a) => (
                <MenuItem key={a.id} value={a.id}>
                  {a.name}
                </MenuItem>
              ))}
          </Select>
        )}
      />

      <Controller
        name={`isolationRules.${ruleIndex}.conditions.${condIndex}.isUnmatch`}
        control={control}
        render={({ field }) => (
          <Checkbox
            size="small"
            checked={field.value}
            onChange={(e) => field.onChange(e.target.checked)}
            title="NOT"
          />
        )}
      />

      <Box flexGrow={1} minWidth={150}>
        {selectedAttr && selectedAttr.type !== 0 ? (
          <IsolationConditionValue
            ruleIndex={ruleIndex}
            condIndex={condIndex}
            attrType={selectedAttr.type}
            attrId={selectedAttr.id}
            control={control}
          />
        ) : (
          <TextField
            variant="standard"
            fullWidth
            size="small"
            disabled
            placeholder="値"
          />
        )}
      </Box>

      <IconButton size="small" onClick={onRemove}>
        <DeleteOutlineIcon />
      </IconButton>
      <IconButton size="small" onClick={onAddAfter}>
        <AddIcon />
      </IconButton>
    </Box>
  );
};

interface RuleRowProps {
  ruleIndex: number;
  control: Control<Schema>;
  savedAttrs: Array<{ id?: number; name: string; type: number }>;
  referralEntities: Entity[];
  onRemove: () => void;
  onAddAfter: () => void;
}

const IsolationRuleRow: FC<RuleRowProps> = ({
  ruleIndex,
  control,
  savedAttrs,
  referralEntities,
  onRemove,
  onAddAfter,
}) => {
  const isPreventAll = useWatch({
    control,
    name: `isolationRules.${ruleIndex}.action.isPreventAll`,
  });

  return (
    <StyledTableRow>
      <TableCell>
        <Controller
          name={`isolationRules.${ruleIndex}.action.preventFrom`}
          control={control}
          render={({ field }) => (
            <Autocomplete
              options={referralEntities}
              getOptionLabel={(opt) => opt.name}
              isOptionEqualToValue={(opt, val) => opt.id === val.id}
              value={field.value ?? null}
              onChange={(_e, val) => field.onChange(val)}
              disabled={isPreventAll}
              size="small"
              sx={{ minWidth: 150 }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  placeholder="モデルを選択"
                  size="small"
                />
              )}
            />
          )}
        />
      </TableCell>

      <TableCell>
        <Controller
          name={`isolationRules.${ruleIndex}.action.isPreventAll`}
          control={control}
          render={({ field }) => (
            <Checkbox
              checked={field.value}
              onChange={(e) => field.onChange(e.target.checked)}
            />
          )}
        />
      </TableCell>

      <TableCell>
        <IsolationConditionsCell
          ruleIndex={ruleIndex}
          control={control}
          savedAttrs={savedAttrs}
        />
      </TableCell>

      <TableCell>
        <IconButton onClick={onRemove}>
          <DeleteOutlineIcon />
        </IconButton>
      </TableCell>

      <TableCell>
        <IconButton onClick={onAddAfter}>
          <AddIcon />
        </IconButton>
      </TableCell>
    </StyledTableRow>
  );
};

const emptyRule = () => ({
  id: undefined,
  conditions: [],
  action: {
    id: undefined,
    isPreventAll: false,
    preventFrom: null,
  },
});

export const IsolationRulesFields: FC<Props> = ({
  control,
  referralEntities,
}) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: "isolationRules",
    keyName: "key",
  });

  const formAttrs = useWatch({ control, name: "attrs" });
  const savedAttrs = (formAttrs ?? []).filter((a) => a.id !== undefined);

  return (
    <>
      <Typography variant="h4" align="center" my="16px">
        他アイテムから参照されなくなる設定
      </Typography>

      <Table id="table_isolation_rules_list">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell width="200px">対象モデル</HeaderTableCell>
            <HeaderTableCell width="100px">全モデル</HeaderTableCell>
            <HeaderTableCell sx={{ display: "flex", gap: "8px" }}>
              <Box width="200px">除外条件</Box>
              <Box>NOT</Box>
            </HeaderTableCell>
            <HeaderTableCell width="60px">削除</HeaderTableCell>
            <HeaderTableCell width="60px">追加</HeaderTableCell>
          </HeaderTableRow>
        </TableHead>
        <TableBody>
          {fields.map((rule, ruleIndex) => (
            <IsolationRuleRow
              key={rule.key}
              ruleIndex={ruleIndex}
              control={control}
              savedAttrs={savedAttrs}
              referralEntities={referralEntities}
              onRemove={() => remove(ruleIndex)}
              onAddAfter={() => insert(ruleIndex + 1, emptyRule())}
            />
          ))}
          {fields.length === 0 && (
            <StyledTableRow>
              <TableCell />
              <TableCell />
              <TableCell />
              <TableCell />
              <TableCell>
                <IconButton onClick={() => insert(0, emptyRule())}>
                  <AddIcon />
                </IconButton>
              </TableCell>
            </StyledTableRow>
          )}
        </TableBody>
      </Table>
    </>
  );
};
