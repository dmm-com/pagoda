import { execFileSync, spawn } from "node:child_process";
import { once } from "node:events";
import {
	closeSync,
	existsSync,
	mkdirSync,
	mkdtempSync,
	openSync,
	readFileSync,
	writeFileSync,
} from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { parseArgs } from "node:util";

const root = resolve(import.meta.dirname, "../..");
const configPath = "tools/mutation/mutator.config.json";
const cli = join(import.meta.dirname, "node_modules/.bin/mutator");

async function main() {
	const { values } = parseArgs({
		options: {
			help: { type: "boolean", short: "h" },
			since: { type: "string" },
			include: { type: "string", multiple: true },
			only: { type: "string", multiple: true },
			all: { type: "boolean" },
			"time-budget": { type: "string", default: "120" },
		},
	});
	if (values.help) {
		console.log(`Usage: npm run test:mutation -- [options]
  --since <ref>         Compare against this commit (default: HEAD)
  --include <file>      Replace the default scope with a frontend source path (repeatable)
  --only <id>           Recheck a mutant in the selected scope (repeatable)
  --all                 Inspect the selected scope without a Git diff
  --time-budget <sec>   Stop starting mutants after this budget (default: 120)

Setup on macOS or Linux with Node 24+: npm ci --prefix tools/mutation --ignore-scripts`);
		return;
	}
	if (
		Number(process.versions.node.split(".")[0]) < 24 ||
		process.platform === "win32"
	) {
		throw new Error("Mutation testing requires Node 24+ on macOS or Linux.");
	}
	if (!existsSync(join(root, "node_modules/vitest/package.json"))) {
		throw new Error("Install frontend dependencies with npm ci first.");
	}
	if (!existsSync(cli)) {
		throw new Error(
			"Run npm ci --prefix tools/mutation --ignore-scripts with Node 24+.",
		);
	}
	if (values.all && (values.only || values.since)) {
		throw new Error("--all cannot be combined with --since or --only.");
	}
	const budget = Number(values["time-budget"]);
	if (!Number.isInteger(budget) || budget < 1 || budget > 1800) {
		throw new Error(
			"--time-budget must be an integer between 1 and 1800 seconds.",
		);
	}

	const since = values.since ?? (values.all || values.only ? null : "HEAD");
	const base = since !== null
		? execFileSync(
				"git",
				["rev-parse", "--verify", "--end-of-options", `${since}^{commit}`],
				{ cwd: root, encoding: "utf8" },
			).trim()
		: null;
	const scope =
		values.include ??
		JSON.parse(readFileSync(join(root, configPath), "utf8")).include;
	if (
		scope.some(
			(file) =>
				!/^frontend\/src\/[\w./-]+\.tsx?$/.test(file) ||
				relative(root, resolve(root, file)) !== file,
		)
	) {
		throw new Error(
			"--include expects a repository-relative .ts or .tsx path under frontend/src.",
		);
	}
	for (const file of values.include ?? []) {
		if (!existsSync(join(root, file))) {
			throw new Error(`--include source does not exist: ${file}`);
		}
	}
	const runs = join(root, ".mutator/pagoda/runs");
	mkdirSync(runs, { recursive: true });
	const directory = mkdtempSync(join(runs, "run-"));
	const agentPath = join(directory, "agent.json");
	const logPath = join(directory, "run.log");
	const args = [
		"--runner",
		"vitest",
		"--config",
		"vitest.config.ts",
		"--config-file",
		configPath,
		"--time-budget",
		String(budget),
		"--report-dir",
		directory,
		"--reporter",
		"agent",
		"--reporter",
		"json",
		...scope.flatMap((glob) => ["--include", glob]),
		...(values.only ?? []).flatMap((id) => ["--only", id]),
		...(base ? ["--since", base, "--include-test-changes"] : []),
	];

	console.log(`Mutation output: ${relative(root, directory)}`);
	console.log(`Scope: ${scope.join(", ")}`);
	const stdout = openSync(agentPath, "w");
	const stderr = openSync(logPath, "w");
	const originalPath = `${dirname(process.execPath)}:${process.env.PATH ?? ""}`;
	const child = spawn(process.execPath, [cli, ...args], {
		cwd: root,
		detached: true,
		env: {
			...process.env,
			PATH: `${join(import.meta.dirname, "git-bin")}:${originalPath}`,
			NODE_ENV: "test",
			PAGODA_MUTATION: "1",
			PAGODA_MUTATION_ORIGINAL_PATH: originalPath,
			PAGODA_MUTATION_ROOT: root,
			TZ: "UTC",
		},
		stdio: ["ignore", stdout, stderr],
	});
	closeSync(stdout);
	closeSync(stderr);

	let interrupted = null;
	function stop(signal) {
		interrupted = signal;
		if (!child.pid) return;
		try {
			process.kill(-child.pid, "SIGKILL");
		} catch (error) {
			if (error.code !== "ESRCH") throw error;
		}
	}
	const limit = setTimeout(() => stop("timeout"), (budget + 60) * 1000);
	const onInterrupt = () => stop("SIGINT");
	const onTerminate = () => stop("SIGTERM");
	process.once("SIGINT", onInterrupt);
	process.once("SIGTERM", onTerminate);
	let exitCode;
	try {
		const [code] = await once(child, "close");
		exitCode =
			{ timeout: 124, SIGINT: 130, SIGTERM: 143 }[interrupted] ?? code ?? 1;
	} finally {
		clearTimeout(limit);
		process.off("SIGINT", onInterrupt);
		process.off("SIGTERM", onTerminate);
	}
	writeFileSync(
		join(directory, "run.json"),
		`${JSON.stringify(
			{
				node: process.version,
				base,
				scope,
				budget,
				only: values.only ?? [],
				exitCode,
			},
			null,
			2,
		)}\n`,
	);
	if (exitCode !== 0) {
		console.error(
			`Mutation run exited with ${exitCode}. See ${relative(root, logPath)}.`,
		);
		process.exitCode = exitCode;
		return;
	}

	const report = JSON.parse(readFileSync(agentPath, "utf8"));
	if (report.version !== 1)
		throw new Error("Unexpected mutator agent report version.");
	const counts = Object.entries(report.counts).map(
		([status, count]) => `${status}=${count}`,
	);
	console.log(
		counts.length ? counts.join(", ") : "No mutants selected for this run.",
	);
	console.log(
		`Previous snapshot: ${report.comparison}. Runner warnings: ${report.warnings.length}.`,
	);
	const regressions = new Set(
		report.findings
			.filter((finding) => finding.kind === "detectionRegression")
			.map((finding) => finding.key),
	);
	console.log(`Detection regressions: ${regressions.size}.`);
	const gaps = report.gaps.sort(
		(a, b) => Number(regressions.has(b.key)) - Number(regressions.has(a.key)),
	);
	for (const gap of gaps.slice(0, 3)) {
		console.log(`  ${gap.key} ${gap.gap} ${gap.file}:${gap.line}`);
	}
	console.log(`Details: ${relative(root, agentPath)}`);
}

try {
	await main();
} catch (error) {
	console.error(error.message);
	process.exitCode = 1;
}
