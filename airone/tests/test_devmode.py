import os
import tempfile
from unittest import TestCase, mock

from airone.lib import devmode


class SlotTest(TestCase):
    """The slot is what keeps two worktrees off each other's port and database."""

    def _with_workspace(self, path):
        return mock.patch.object(devmode, "workspace_path", return_value=path)

    def test_slot_is_stable_for_a_path(self):
        with self._with_workspace("/repos/pagoda/worktrees/feature-a"):
            first = devmode.slot()
            second = devmode.slot()
        self.assertEqual(first, second)

    def test_slot_differs_between_checkouts(self):
        with self._with_workspace("/repos/pagoda/worktrees/feature-a"):
            a = devmode.slot()
        with self._with_workspace("/repos/pagoda/worktrees/feature-b"):
            b = devmode.slot()
        self.assertNotEqual(a, b)

    def test_slot_stays_inside_the_slot_space(self):
        for name in ("alpha", "beta", "gamma", "delta", "epsilon"):
            with self._with_workspace("/repos/pagoda/worktrees/%s" % name):
                self.assertIn(devmode.slot(), range(devmode.SLOT_SPACE))

    def test_slot_can_be_pinned(self):
        with mock.patch.dict(os.environ, {"PAGODA_SLOT": "7"}):
            self.assertEqual(devmode.slot(), 7)

    def test_pinned_slot_wraps_into_the_slot_space(self):
        with mock.patch.dict(os.environ, {"PAGODA_SLOT": str(devmode.SLOT_SPACE + 3)}):
            self.assertEqual(devmode.slot(), 3)


class PortTest(TestCase):
    def test_port_is_offset_from_the_base(self):
        with mock.patch.dict(os.environ, {"PAGODA_SLOT": "12"}):
            self.assertEqual(devmode.port(), devmode.DEFAULT_PORT_BASE + 12)

    def test_port_base_is_overridable(self):
        with mock.patch.dict(os.environ, {"PAGODA_SLOT": "12", "PAGODA_PORT_BASE": "9000"}):
            self.assertEqual(devmode.port(), 9012)

    def test_container_ports_are_offset_too(self):
        with mock.patch.dict(os.environ, {"PAGODA_SLOT": "5"}):
            self.assertEqual(devmode.service_port("MYSQL"), 3311)
            self.assertEqual(devmode.service_port("ES"), 9205)
            self.assertEqual(devmode.service_port("RABBITMQ"), 5677)

    def test_two_checkouts_do_not_share_a_port(self):
        with mock.patch.object(devmode, "workspace_path", return_value="/w/one"):
            one = devmode.port()
        with mock.patch.object(devmode, "workspace_path", return_value="/w/two"):
            two = devmode.port()
        self.assertNotEqual(one, two)


class NamespaceTest(TestCase):
    def test_namespace_combines_name_and_slot(self):
        with mock.patch.object(devmode, "workspace_path", return_value="/repos/my-feature"):
            with mock.patch.dict(os.environ, {"PAGODA_SLOT": "3"}):
                self.assertEqual(devmode.namespace(), "my-feature-03")

    def test_namespace_is_safe_for_index_names_and_paths(self):
        with mock.patch.object(devmode, "workspace_path", return_value="/repos/Feature/Wip #2!"):
            with mock.patch.dict(os.environ, {"PAGODA_SLOT": "0"}):
                namespace = devmode.namespace()
        # "Wip #2!" -> lowercased, every non-alnum becomes "-", trailing ones trimmed
        self.assertEqual(namespace, "wip--2-00")
        self.assertTrue(all(c.isalnum() or c in "-_" for c in namespace), namespace)

    def test_namespace_never_collapses_to_nothing(self):
        with mock.patch.object(devmode, "workspace_path", return_value="/repos/###"):
            with mock.patch.dict(os.environ, {"PAGODA_SLOT": "0"}):
                self.assertEqual(devmode.namespace(), "pagoda-00")

    def test_compose_project_is_per_checkout(self):
        with mock.patch.object(devmode, "workspace_path", return_value="/repos/my-feature"):
            with mock.patch.dict(os.environ, {"PAGODA_SLOT": "3"}):
                self.assertEqual(devmode.compose_project(), "pagoda-my-feature-03")


class StateDirTest(TestCase):
    def test_state_dir_defaults_inside_the_checkout(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PAGODA_STATE_DIR", None)
            self.assertTrue(devmode.state_dir().endswith("/.pagoda-lite"))

    def test_state_dir_is_overridable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"PAGODA_STATE_DIR": tmp}):
                self.assertEqual(devmode.state_dir(), os.path.realpath(tmp))

    def test_ensure_state_dir_creates_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "nested", "state")
            with mock.patch.dict(os.environ, {"PAGODA_STATE_DIR": target}):
                devmode.ensure_state_dir()
            self.assertTrue(os.path.isdir(target))

    def test_sqlite_url_points_at_the_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"PAGODA_STATE_DIR": tmp}):
                url = devmode.sqlite_url()
        self.assertTrue(url.startswith("sqlite:///"))
        self.assertTrue(url.endswith("pagoda.sqlite3"))

    def test_two_checkouts_do_not_share_a_database_file(self):
        with mock.patch.object(devmode, "_repo_root", return_value="/repos/one"):
            one = devmode.sqlite_url()
        with mock.patch.object(devmode, "_repo_root", return_value="/repos/two"):
            two = devmode.sqlite_url()
        self.assertNotEqual(one, two)


class LiteFlagTest(TestCase):
    def test_recognised_truthy_values(self):
        for value in ("1", "true", "TRUE", "yes", "on"):
            with mock.patch.dict(os.environ, {"PAGODA_LITE": value}):
                self.assertTrue(devmode.is_lite(), value)

    def test_everything_else_is_off(self):
        for value in ("", "0", "false", "no", "off", "maybe"):
            with mock.patch.dict(os.environ, {"PAGODA_LITE": value}):
                self.assertFalse(devmode.is_lite(), value)

    def test_absent_means_off(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PAGODA_LITE", None)
            self.assertFalse(devmode.is_lite())


class CommandLineTest(TestCase):
    """tools/lite.sh eval()s --env, so its shape is load-bearing."""

    def _run(self, argv):
        with mock.patch("sys.stdout") as stdout:
            devmode.main(argv)
        return "".join(call.args[0] for call in stdout.write.call_args_list)

    def test_env_output_is_shell_exports(self):
        with mock.patch.dict(os.environ, {"PAGODA_SLOT": "8"}):
            output = self._run(["--env"])
        self.assertIn("export PAGODA_SLOT=8", output)
        self.assertIn("export PAGODA_PORT=", output)
        self.assertIn("export COMPOSE_PROJECT_NAME=", output)
        for line in output.splitlines():
            if line.strip():
                self.assertRegex(line, r"^export [A-Z_]+=\S*$")

    def test_json_output_is_parseable(self):
        import json

        payload = json.loads(self._run(["--json"]))
        self.assertEqual(
            set(payload) & {"slot", "port", "namespace", "state_dir"},
            {"slot", "port", "namespace", "state_dir"},
        )

    def test_summary_lists_the_container_ports(self):
        self.assertEqual(set(devmode.summary()["container_ports"]), set(devmode.SERVICE_PORT_BASES))
