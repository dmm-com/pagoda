import enum


@enum.unique
class JobOperationCustom(enum.IntEnum):
    UPDATE_CUSTOM_ATTRIBUTE = 101


CUSTOM_HIDDEN_OPERATIONS: list[JobOperationCustom] = []
CUSTOM_CANCELABLE_OPERATIONS: list[JobOperationCustom] = []
CUSTOM_PARALLELIZABLE_OPERATIONS: list[JobOperationCustom] = [
    JobOperationCustom.UPDATE_CUSTOM_ATTRIBUTE
]
CUSTOM_DOWNLOADABLE_OPERATIONS: list[JobOperationCustom] = []
CUSTOM_TASKS: dict[JobOperationCustom, str] = {
    JobOperationCustom.UPDATE_CUSTOM_ATTRIBUTE: "update_custom_attribute",
}
