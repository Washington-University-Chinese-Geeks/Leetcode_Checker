/**
 * Filesystem-backed data loader.
 *
 * All of these functions run at build time (Next.js static export), so they
 * can read directly from the committed `data/` directory via `node:fs`.
 * Never import this module from a Client Component — it would drag `fs`
 * into the browser bundle.
 */
import fs from "node:fs";
import path from "node:path";

import type {
  BenchmarkEntry,
  BenchmarkPeriod,
  Benchmarks,
  Summary,
  UserRecord,
} from "./types";

// web/lib/data.ts -> up to repo root -> data/
const DATA_DIR = path.resolve(process.cwd(), "..", "data");
const USERS_DIR = path.join(DATA_DIR, "users");

function readJsonIfExists<T>(filePath: string): T | null {
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as T;
}

export function loadSummary(): Summary {
  const summary = readJsonIfExists<Summary>(path.join(DATA_DIR, "summary.json"));
  if (summary) return summary;
  // Empty fallback keeps the site buildable before the first collector run.
  return {
    generated_at: new Date(0).toISOString(),
    member_count: 0,
    members: [],
  };
}

export function loadAllUsers(): UserRecord[] {
  if (!fs.existsSync(USERS_DIR)) return [];
  const files = fs.readdirSync(USERS_DIR).filter((f) => f.endsWith(".json"));
  return files
    .map((file) => readJsonIfExists<UserRecord>(path.join(USERS_DIR, file)))
    .filter((u): u is UserRecord => u !== null);
}

export function loadUserBySlug(slug: string): UserRecord | null {
  const direct = readJsonIfExists<UserRecord>(path.join(USERS_DIR, `${slug}.json`));
  if (direct) return direct;
  // Fallback: scan directory in case slugging rules diverge.
  return (
    loadAllUsers().find(
      (u) => u.leetcode_username.toLowerCase() === slug.toLowerCase(),
    ) ?? null
  );
}

export function listUserSlugs(): string[] {
  if (!fs.existsSync(USERS_DIR)) return [];
  return fs
    .readdirSync(USERS_DIR)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.slice(0, -".json".length));
}

const WINDOW_SECONDS: Record<BenchmarkPeriod, number> = {
  daily: 24 * 60 * 60,
  weekly: 7 * 24 * 60 * 60,
  monthly: 30 * 24 * 60 * 60,
};

function countSubmissionsInWindow(user: UserRecord, windowSec: number, nowSec: number): number {
  const cutoff = nowSec - windowSec;
  let n = 0;
  for (const s of user.recent_submissions) {
    const ts = Number(s.timestamp);
    if (!Number.isFinite(ts) || ts <= 0) continue;
    if (ts >= cutoff) n += 1;
  }
  return n;
}

export function loadBenchmarks(users?: UserRecord[]): Benchmarks {
  const all = users ?? loadAllUsers();
  const nowSec = Math.floor(Date.now() / 1000);

  const build = (period: BenchmarkPeriod): BenchmarkEntry[] => {
    const w = WINDOW_SECONDS[period];
    return all
      .map<BenchmarkEntry>((u) => ({
        leetcode_username: u.leetcode_username,
        display_name: u.display_name,
        server_region: u.server_region,
        count: countSubmissionsInWindow(u, w, nowSec),
      }))
      .sort((a, b) => b.count - a.count || a.display_name.localeCompare(b.display_name));
  };

  return {
    daily: build("daily"),
    weekly: build("weekly"),
    monthly: build("monthly"),
  };
}
