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

import type { Summary, UserRecord } from "./types";

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
