import { findDuplicateIndexes } from "./Edit";

test("findDuplicateIndexes() returns attr indexes have duplicated name", () => {
  const actual = findDuplicateIndexes([
    {
      name: "unique1",
      type: 2,
      isMandatory: false,
      isDeleteInChain: false,
      isSummarized: false,
      isWritable: false,
      referral: [],
      note: "note1",
    },
    // duplicated with index=2
    {
      name: "duplicated1",
      type: 2,
      isMandatory: false,
      isDeleteInChain: false,
      isSummarized: false,
      isWritable: false,
      referral: [],
      note: "note2",
    },
    // duplicated with index=1
    {
      name: "duplicated1",
      type: 2,
      isMandatory: false,
      isDeleteInChain: false,
      isSummarized: false,
      isWritable: false,
      referral: [],
      note: "note3",
    },
    {
      name: "unique2",
      type: 2,
      isMandatory: false,
      isDeleteInChain: false,
      isSummarized: false,
      isWritable: false,
      referral: [],
      note: "note4",
    },
    // duplicated with index=5
    {
      name: "duplicated2",
      type: 2,
      isMandatory: false,
      isDeleteInChain: false,
      isSummarized: false,
      isWritable: false,
      referral: [],
      note: "note5",
    },
    // duplicated with index=4
    {
      name: "duplicated2",
      type: 2,
      isMandatory: false,
      isDeleteInChain: false,
      isSummarized: false,
      isWritable: false,
      referral: [],
      note: "note6",
    },
  ]);

  expect(actual).toEqual([2, 1, 5, 4]);
});
