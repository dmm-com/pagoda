import { GroupTree } from "../../apiclient/AironeApiClientV2";

import { filterAncestorsAndOthers } from "./Edit";

test("filterAncestorsAndOthers returns group trees without specific group and their descendants", () => {
  const groupTrees: GroupTree[] = [
    {
      id: 1,
      name: "group1",
      children: [
        {
          id: 11,
          name: "group11",
          children: [
            {
              id: 111,
              name: "group111",
              children: [],
            },
          ],
        },
        {
          id: 12,
          name: "group12",
          children: [
            {
              id: 121,
              name: "group121",
              children: [],
            },
          ],
        },
      ],
    },
    {
      id: 2,
      name: "group2",
      children: [
        {
          id: 21,
          name: "group21",
          children: [
            {
              id: 211,
              name: "group211",
              children: [],
            },
          ],
        },
        {
          id: 22,
          name: "group22",
          children: [
            {
              id: 221,
              name: "group221",
              children: [],
            },
          ],
        },
      ],
    },
  ];
  const targetGroupId = 11;

  const actual = filterAncestorsAndOthers(groupTrees, targetGroupId);

  expect(actual).toStrictEqual([
    {
      id: 1,
      name: "group1",
      children: [
        // group(id=11) and their descendants are filtered
        {
          id: 12,
          name: "group12",
          children: [
            {
              id: 121,
              name: "group121",
              children: [],
            },
          ],
        },
      ],
    },
    {
      id: 2,
      name: "group2",
      children: [
        {
          id: 21,
          name: "group21",
          children: [
            {
              id: 211,
              name: "group211",
              children: [],
            },
          ],
        },
        {
          id: 22,
          name: "group22",
          children: [
            {
              id: 221,
              name: "group221",
              children: [],
            },
          ],
        },
      ],
    },
  ]);
});
