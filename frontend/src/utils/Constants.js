const BaseAttributeTypes = {
  object: 1 << 0,
  string: 1 << 1,
  text: 1 << 2,
  bool: 1 << 3,
  group: 1 << 4,
  date: 1 << 5,
  array: 1 << 10,
  named: 1 << 11,
};

export const AttributeTypes = {
  object: BaseAttributeTypes.object,
  string: BaseAttributeTypes.string,
  named: BaseAttributeTypes.named,
  named_object: BaseAttributeTypes.object | BaseAttributeTypes.named,
  array: BaseAttributeTypes.array,
  array_object: BaseAttributeTypes.object | BaseAttributeTypes.array,
  array_string: BaseAttributeTypes.string | BaseAttributeTypes.array,
  array_named_object:
    BaseAttributeTypes.object |
    BaseAttributeTypes.named |
    BaseAttributeTypes.array,
  array_group: BaseAttributeTypes.group | BaseAttributeTypes.array,
  text: BaseAttributeTypes.text,
  boolean: BaseAttributeTypes.bool,
  group: BaseAttributeTypes.group,
  date: BaseAttributeTypes.date,
};

export const EntityStatus = {
  TOP_LEVEL: 1 << 0,
  CREATING: 1 << 1,
  EDITING: 1 << 2,
};
