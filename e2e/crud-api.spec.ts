import { expect, test } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";

const attributeTypes = [
  ["string", 2], ["array_string", 1026], ["object", 1],
  ["array_object", 1025], ["named_object", 2049],
  ["array_named_object", 3073], ["group", 16], ["array_group", 1040],
  ["role", 64], ["array_role", 1088], ["text", 4], ["boolean", 8],
  ["date", 32], ["datetime", 128], ["number", 256],
  ["array_number", 1280], ["select", 512], ["multi_select", 1536],
] as const;

const crud = async (
  request: APIRequestContext,
  base: string,
  wrapper: string,
  createData: Record<string, unknown>,
  updateData: Record<string, unknown>,
) => {
  const response = await request.post(base, { data: { [wrapper]: createData } });
  expect(response.status()).toBe(201);
  const created = await response.json();
  expect(await (await request.get(`${base}/${created.id}`)).json()).toMatchObject(createData);
  const updated = await request.put(`${base}/${created.id}`, { data: { [wrapper]: updateData } });
  expect(updated.status()).toBe(200);
  expect(await updated.json()).toMatchObject(updateData);
  expect((await request.delete(`${base}/${created.id}`)).status()).toBe(204);
  expect((await request.get(`${base}/${created.id}`)).status()).toBe(404);
};

test.beforeEach(async ({ request }) => {
  expect((await request.post("/__e2e/reset")).status()).toBe(204);
});

test("@crud @entity covers CRUD with every supported attribute type", async ({ request }) => {
  const attrs = attributeTypes.map(([name, type], index) => ({
    name, type, index, isMandatory: false, isDeleteInChain: false,
    isSummarized: index === 0, referral: type & 1 ? [2] : [],
    choices: type & 512 ? ["one", "two"] : null,
  }));
  const response = await request.post("/entity/api/v2", { data: { entityCreate: {
    name: "All Attribute Types", note: "E2E exhaustive entity",
    itemNamePattern: "^.+$", itemNameType: "US", isToplevel: true, attrs,
  } } });
  expect(response.status()).toBe(201);
  const created = await response.json();
  expect(created.attrs.map(({ type }: { type: number }) => type)).toEqual(attributeTypes.map(([, type]) => type));
  expect((await request.get(`/entity/api/v2/${created.id}`)).status()).toBe(200);
  expect((await request.put(`/entity/api/v2/${created.id}`, { data: { entityUpdate: { name: "All Attribute Types Updated" } } })).status()).toBe(200);
  expect((await request.delete(`/entity/api/v2/${created.id}`)).status()).toBe(204);
});

test("@crud @entry covers CRUD with values for every attribute type", async ({ request }) => {
  const attrs = attributeTypes.map(([name, type], index) => ({ id: 100 + index, type, name, value: { raw: `fixture-${name}` } }));
  const response = await request.post("/entity/api/v2/1/entries", { data: { entryCreate: { name: "all-values", attrs } } });
  expect(response.status()).toBe(201);
  const created = await response.json();
  expect(created.submitted_attrs).toHaveLength(attributeTypes.length);
  expect(created.submitted_attrs.map(({ type }: { type: number }) => type)).toEqual(
    attributeTypes.map(([, type]) => type),
  );
  expect((await request.get(`/entry/api/v2/${created.id}`)).status()).toBe(200);
  expect((await request.put(`/entry/api/v2/${created.id}`, { data: { entryUpdate: { name: "all-values-updated", attrs } } })).status()).toBe(200);
  expect((await request.delete(`/entry/api/v2/${created.id}`)).status()).toBe(204);
});

test("@crud @user CRUD", async ({ request }) => crud(request, "/user/api/v2", "userCreate", { username: "e2e-user", email: "e2e@example.test" }, { username: "e2e-user-updated" }));
test("@crud @group CRUD", async ({ request }) => crud(request, "/group/api/v2/groups", "groupCreateUpdate", { name: "E2E Group", members: [] }, { name: "E2E Group Updated" }));
test("@crud @role CRUD", async ({ request }) => crud(request, "/role/api/v2", "roleCreateUpdate", { name: "E2E Role", description: "created" }, { name: "E2E Role Updated" }));

test("@advanced-search submits criteria and reads results", async ({ request }) => {
  const criteria = { entities: [1], attrinfo: attributeTypes.map(([name, type]) => ({ name, type })), isAllEntities: false, hasReferral: true };
  const response = await request.post("/entry/api/v2/advanced_search", { data: { advancedSearch: criteria } });
  expect(response.status()).toBe(200);
  const results = await response.json();
  expect(results.requested_criteria).toEqual(criteria);
  expect(results.values.length).toBeGreaterThan(0);
});
