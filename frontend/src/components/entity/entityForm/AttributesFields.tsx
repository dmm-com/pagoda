import { Entity } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  DndContext,
  DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { restrictToVerticalAxis } from "@dnd-kit/modifiers";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, useState } from "react";
import {
  Control,
  FieldArrayWithId,
  useFieldArray,
  useWatch,
} from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { AttributeField } from "./AttributeField";
import { Schema } from "./EntityFormSchema";

import { AttributeTypes } from "services/Constants";

const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({}) => ({
  color: "#FFFFFF",
  boxSizing: "border-box",
}));

const StyledTableBody = styled(TableBody)({
  "tr:nth-of-type(odd)": {
    backgroundColor: "white",
  },
  "tr:nth-of-type(even)": {
    backgroundColor: "#607D8B0A",
  },
  "& td": {
    padding: "8px",
  },
});

const highlightedRowSx = {
  "@keyframes highlighted": {
    from: {
      backgroundColor: "#6B8998",
    },
  },
  animation: "highlighted 1s ease 0s 1",
};

/**
 * Compute the source/destination indices of a drag-and-drop reorder.
 *
 * Returns null when the drop is a no-op (dropped on itself or an unknown id),
 * so callers can skip mutating the field array.
 */
export const getReorderIndices = (
  ids: string[],
  activeId: string,
  overId: string,
): { oldIndex: number; newIndex: number } | null => {
  if (activeId === overId) {
    return null;
  }
  const oldIndex = ids.indexOf(activeId);
  const newIndex = ids.indexOf(overId);
  if (oldIndex < 0 || newIndex < 0) {
    return null;
  }
  return { oldIndex, newIndex };
};

interface SortableAttributeRowProps {
  field: FieldArrayWithId<Schema, "attrs", "key">;
  index: number;
  isHighlighted: boolean;
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  referralEntities: Entity[];
  handleAppendAttribute: (index: number) => void;
  handleDeleteAttribute: (index: number) => void;
}

const SortableAttributeRow: FC<SortableAttributeRowProps> = ({
  field,
  index,
  isHighlighted,
  control,
  setValue,
  referralEntities,
  handleAppendAttribute,
  handleDeleteAttribute,
}) => {
  const isWritable = useWatch({
    control,
    name: `attrs.${index}.isWritable`,
  });

  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: field.key, disabled: !isWritable });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    ...(isDragging
      ? { position: "relative" as const, zIndex: 1, opacity: 0.7 }
      : {}),
  };

  return (
    <TableRow
      ref={setNodeRef}
      style={style}
      sx={isHighlighted ? highlightedRowSx : undefined}
    >
      <AttributeField
        referralEntities={referralEntities}
        handleAppendAttribute={handleAppendAttribute}
        handleDeleteAttribute={handleDeleteAttribute}
        control={control}
        setValue={setValue}
        attrId={field.id}
        index={index}
        dragHandleProps={{
          setActivatorNodeRef,
          attributes,
          listeners,
          isDragging,
        }}
      />
    </TableRow>
  );
};

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  referralEntities: Entity[];
}

export const AttributesFields: FC<Props> = ({
  control,
  setValue,
  referralEntities,
}) => {
  const { fields, insert, remove, move } = useFieldArray({
    control,
    name: "attrs",
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  const [latestChangedIndex, setLatestChangedIndex] = useState<number | null>(
    null,
  );

  const sensors = useSensors(
    // Require a small drag distance so clicks on nested inputs are not swallowed
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    // Keep keyboard-based reordering available for accessibility
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const handleAppendAttribute = (index: number) => {
    insert(index + 1, {
      name: "",
      type: AttributeTypes.string.type,
      isMandatory: false,
      isDeleteInChain: false,
      isSummarized: false,
      isWritable: true,
      referral: [],
      note: "",
      defaultValue: undefined, // Explicitly initialize defaultValue
      nameOrder: "0",
      namePrefix: "",
      namePostfix: "",
      displayAttr: "",
    });
  };

  const handleDeleteAttribute = (index: number) => {
    remove(index);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over == null) {
      return;
    }
    const indices = getReorderIndices(
      fields.map((field) => field.key),
      String(active.id),
      String(over.id),
    );
    if (indices == null) {
      return;
    }
    move(indices.oldIndex, indices.newIndex);
    setLatestChangedIndex(indices.newIndex);
  };

  return (
    <>
      <Typography variant="h4" align="center" my="16px">
        属性情報
      </Typography>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        modifiers={[restrictToVerticalAxis]}
        onDragEnd={handleDragEnd}
      >
        <Table id="table_attribute_list">
          <TableHead>
            <HeaderTableRow>
              <HeaderTableCell width="100px">並び替え</HeaderTableCell>
              <HeaderTableCell width="300px">属性名</HeaderTableCell>
              <HeaderTableCell width="300px">型</HeaderTableCell>
              <HeaderTableCell width="200px">デフォルト値</HeaderTableCell>
              <HeaderTableCell width="100px">削除</HeaderTableCell>
              <HeaderTableCell width="100px">追加</HeaderTableCell>
              <HeaderTableCell width="100px">詳細</HeaderTableCell>
            </HeaderTableRow>
          </TableHead>
          <StyledTableBody>
            <SortableContext
              items={fields.map((field) => field.key)}
              strategy={verticalListSortingStrategy}
            >
              {fields.map((field, index) => (
                <SortableAttributeRow
                  key={field.key}
                  field={field}
                  index={index}
                  isHighlighted={index === latestChangedIndex}
                  referralEntities={referralEntities}
                  handleAppendAttribute={handleAppendAttribute}
                  handleDeleteAttribute={handleDeleteAttribute}
                  control={control}
                  setValue={setValue}
                />
              ))}
            </SortableContext>
            {fields.length === 0 && (
              <TableRow>
                <AttributeField
                  referralEntities={referralEntities}
                  handleAppendAttribute={handleAppendAttribute}
                  handleDeleteAttribute={handleDeleteAttribute}
                  control={control}
                  setValue={setValue}
                />
              </TableRow>
            )}
          </StyledTableBody>
        </Table>
      </DndContext>
    </>
  );
};
