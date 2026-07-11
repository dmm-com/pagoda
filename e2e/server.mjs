import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import url from "node:url";
import { fileURLToPath } from "node:url";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(dirname, "..");
const port = Number(process.env.E2E_PORT ?? 4173);

const ACL_FULL = 8;
const refSwitch = { id: 2, name: "Switch" };

const makeAttr = (
  id,
  index,
  name,
  type,
  { referral = [], defaultValue = null } = {},
) => ({
  id,
  index,
  name,
  type,
  is_mandatory: false,
  is_delete_in_chain: false,
  is_summarized: index === 0,
  is_writable: true,
  referral,
  note: `${name} fixture`,
  default_value: defaultValue,
  name_order: 0,
  name_prefix: "",
  name_postfix: "",
});

const attrs = [
  makeAttr(11, 0, "hostname", 2),
  makeAttr(12, 1, "primary_switch", 1, {
    referral: [refSwitch],
  }),
  makeAttr(13, 2, "backup_switches", 1025, {
    referral: [refSwitch],
  }),
  makeAttr(14, 3, "named_switch", 2049, {
    referral: [refSwitch],
  }),
  makeAttr(15, 4, "named_switches", 3073, {
    referral: [refSwitch],
  }),
  makeAttr(16, 5, "description", 4, { defaultValue: "Linux web server" }),
  makeAttr(17, 6, "is_virtual", 8, { defaultValue: true }),
  makeAttr(18, 7, "owner_group", 16),
  makeAttr(19, 8, "installed_on", 32),
  makeAttr(20, 9, "owner_role", 64),
  makeAttr(21, 10, "last_seen_at", 128),
  makeAttr(22, 11, "rack_units", 256, { defaultValue: 2 }),
  makeAttr(23, 12, "aliases", 1026),
  makeAttr(24, 13, "maintenance_groups", 1040),
  makeAttr(25, 14, "support_roles", 1088),
  makeAttr(26, 15, "ports", 1280),
];

const json = (res, status, body) => {
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  res.end(JSON.stringify(body));
};

const switchValue = (id, name) => ({
  id,
  name,
  schema: refSwitch,
});

const serverEntity = {
  id: 1,
  name: "Server",
  note: "Physical and logical server metadata",
  item_name_pattern: "^[a-z0-9-]+$",
  item_name_type: "US",
  is_toplevel: true,
  attrs,
  webhooks: [],
  isolation_rules: [],
  delete_chain_exclude_entities: [],
  is_public: false,
  has_ongoing_changes: false,
  permission: ACL_FULL,
};

const entryDetail = {
  id: 1,
  name: "web-01",
  is_active: true,
  schema: { id: 1, name: "Server", permission: ACL_FULL },
  attrs: [
    attrValue(11, 2, "hostname", { as_string: "web-01.example.test" }),
    attrValue(12, 1, "primary_switch", {
      as_object: switchValue(20, "switch-core-01"),
    }),
    attrValue(13, 1025, "backup_switches", {
      as_array_object: [
        switchValue(21, "switch-backup-01"),
      ],
    }),
    attrValue(14, 2049, "named_switch", {
      as_named_object: {
        name: "uplink",
        object: switchValue(22, "switch-uplink-01"),
      },
    }),
    attrValue(15, 3073, "named_switches", {
      as_array_named_object: [
        {
          name: "standby",
          object: switchValue(23, "switch-standby-01"),
          boolean: false,
        },
      ],
    }),
    attrValue(16, 4, "description", {
      as_string: "Runs the customer-facing web tier.",
    }),
    attrValue(17, 8, "is_virtual", { as_boolean: true }),
    attrValue(18, 16, "owner_group", { as_group: { id: 2, name: "SRE" } }),
    attrValue(19, 32, "installed_on", { as_string: "2026-01-15" }),
    attrValue(20, 64, "owner_role", {
      as_role: { id: 1, name: "Inventory Maintainer" },
    }),
    attrValue(21, 128, "last_seen_at", { as_string: "2026-01-20T10:30:00Z" }),
    attrValue(22, 256, "rack_units", { as_number: 2 }),
    attrValue(23, 1026, "aliases", {
      as_array_string: ["web-primary", "frontend-a"],
    }),
    attrValue(24, 1040, "maintenance_groups", {
      as_array_group: [{ id: 1, name: "Engineering" }, { id: 2, name: "SRE" }],
    }),
    attrValue(25, 1088, "support_roles", {
      as_array_role: [{ id: 1, name: "Inventory Maintainer" }],
    }),
    attrValue(26, 1280, "ports", { as_array_number: [80, 443] }),
  ],
  permission: ACL_FULL,
};

function attrValue(id, type, name, value) {
  return {
    id,
    type,
    is_mandatory: false,
    is_readable: true,
    schema: { id, name, type },
    value,
  };
}

const paginated = (results) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
});

const html = `<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Pagoda E2E</title>
    <script>
      window.django_context = {
        next: "/ui/",
        title: "Pagoda",
        subtitle: "E2E",
        note_desc: "",
        note_link: "",
        version: "e2e",
        user: {
          id: 1,
          username: "admin",
          email: "admin@example.test",
          isSuperuser: true,
          isReadonly: false,
          parentUser: null
        },
        legacyUiDisabled: true,
        password_reset_disabled: false,
        checkTermService: false,
        extendedGeneralParameters: {},
        extendedHeaderMenus: [],
        headerColor: "#1976d2",
        flags: { webhook: true },
        frontendPluginEntityOverrides: {}
      };
    </script>
  </head>
  <body>
    <div id="app"></div>
    <script src="/static/js/ui.js"></script>
  </body>
</html>`;

const serveStatic = (res, pathname) => {
  const filePath = path.join(root, pathname);
  if (!filePath.startsWith(root) || !fs.existsSync(filePath)) return false;
  res.writeHead(200, {
    "Content-Type": pathname.endsWith(".js")
      ? "text/javascript; charset=utf-8"
      : "application/octet-stream",
    "Cache-Control": "no-store",
  });
  fs.createReadStream(filePath).pipe(res);
  return true;
};

const handleApi = (req, res, parsed) => {
  const pathname = parsed.pathname.replace(/\/$/, "");

  if (req.method === "GET" && pathname === "/category/api/v2") {
    json(res, 200, paginated([
      {
        id: 1,
        name: "Operations",
        note: "Operational metadata",
        models: [{ id: 1, name: "Server" }, { id: 2, name: "Switch" }],
        priority: 10,
        permission: ACL_FULL,
      },
    ]));
    return true;
  }
  if (req.method === "GET" && pathname === "/entity/api/v2") {
    json(res, 200, paginated([
      serverEntity,
      {
        id: 2,
        name: "Switch",
        note: "Network switch metadata",
        is_toplevel: true,
        attrs: [],
        permission: ACL_FULL,
      },
    ]));
    return true;
  }
  if (req.method === "GET" && pathname === "/entity/api/v2/1") {
    json(res, 200, serverEntity);
    return true;
  }
  if (req.method === "GET" && pathname === "/entity/api/v2/1/entries") {
    json(res, 200, paginated([
      { id: 1, name: "web-01", schema: { id: 1, name: "Server", permission: ACL_FULL }, is_active: true, aliases: [], permission: ACL_FULL },
      { id: 2, name: "db-01", schema: { id: 1, name: "Server", permission: ACL_FULL }, is_active: true, aliases: [], permission: ACL_FULL },
    ]));
    return true;
  }
  if (req.method === "GET" && pathname === "/entry/api/v2/1") {
    json(res, 200, entryDetail);
    return true;
  }
  if (req.method === "GET" && pathname === "/entry/api/v2/1/referral") {
    json(res, 200, paginated([]));
    return true;
  }
  if (req.method === "GET" && pathname === "/entity/api/v2/attrs") {
    json(res, 200, attrs.map(({ id, name, type }) => ({ id, name, type })));
    return true;
  }
  if (req.method === "GET" && pathname === "/trigger/api/v2") {
    json(res, 200, paginated([]));
    return true;
  }
  if (req.method === "GET" && pathname === "/job/api/v2/jobs") {
    json(res, 200, paginated([]));
    return true;
  }
  return false;
};

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);

  if (parsed.pathname.startsWith("/static/")) {
    if (!serveStatic(res, parsed.pathname)) {
      res.writeHead(404);
      res.end("Not Found");
    }
    return;
  }

  if (handleApi(req, res, parsed)) return;

  if (parsed.pathname.startsWith("/api/") || parsed.pathname.includes("/api/")) {
    json(res, 500, { detail: `Unhandled E2E mock: ${req.method} ${parsed.pathname}` });
    return;
  }

  res.writeHead(200, {
    "Content-Type": "text/html; charset=utf-8",
    "Cache-Control": "no-store",
  });
  res.end(html);
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Pagoda E2E server listening on http://127.0.0.1:${port}`);
});
