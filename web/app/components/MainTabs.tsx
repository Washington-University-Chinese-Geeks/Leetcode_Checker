"use client";

import Link from "next/link";
import { useState } from "react";

import type {
  BenchmarkEntry,
  BenchmarkPeriod,
  Benchmarks,
  SummaryMember,
} from "../../lib/types";

type TabKey = "leaderboard" | "roster" | "benchmarks";

interface LeaderboardRow {
  leetcode_username: string;
  display_name: string;
  server_region: "US" | "CN";
  total_solved: number | null;
  easy: number | null;
  medium: number | null;
  hard: number | null;
}

interface Props {
  members: SummaryMember[];
  leaderboard: LeaderboardRow[];
  benchmarks: Benchmarks;
}

function slugify(username: string): string {
  return (
    username
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9._-]+/g, "-")
      .replace(/^-+|-+$/g, "") || "unknown"
  );
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return (parts[0]![0]! + parts[parts.length - 1]![0]!).toUpperCase();
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "never";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime()) || d.getTime() === 0) return "never";
  return d.toISOString().slice(0, 10);
}

function RosterTab({ members }: { members: SummaryMember[] }) {
  if (members.length === 0) {
    return (
      <div className="empty">
        No member data yet. The collector workflow populates
        <code> data/summary.json</code> on its first successful run.
      </div>
    );
  }
  const sorted = [...members].sort(
    (a, b) => (b.total_solved ?? 0) - (a.total_solved ?? 0),
  );
  return (
    <div className="member-grid">
      {sorted.map((m) => (
        <Link
          key={m.leetcode_username}
          href={`/users/${slugify(m.leetcode_username)}/`}
          className="card"
        >
          <div className="card-head">
            <div className="avatar" aria-hidden="true">
              {initials(m.display_name)}
            </div>
            <div style={{ minWidth: 0 }}>
              <h3>{m.display_name}</h3>
              <div className="card-sub">
                <span>@{m.leetcode_username}</span>
                <span className="chip">{m.server_region}</span>
              </div>
            </div>
          </div>
          <div className="stat">
            <span>Total solved</span>
            <span>{m.total_solved ?? "—"}</span>
          </div>
          <div className="stat">
            <span>AC in plan</span>
            <span>{m.plan_submission_count ?? "—"}</span>
          </div>
          <div className="stat">
            <span>Recent AC</span>
            <span>{m.recent_submission_count ?? 0}</span>
          </div>
          <div className="stat">
            <span>Last AC</span>
            <span>{formatDate(m.last_submission_at)}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}

function LeaderboardTab({ rows }: { rows: LeaderboardRow[] }) {
  if (rows.length === 0) {
    return <div className="empty">No ranking data yet.</div>;
  }
  const sorted = [...rows].sort(
    (a, b) => (b.total_solved ?? 0) - (a.total_solved ?? 0),
  );
  return (
    <div className="rank-list">
      {sorted.map((r, i) => {
        const pos = i + 1;
        const topClass = pos <= 3 ? ` top-${pos}` : "";
        const breakdown = [r.easy ?? 0, r.medium ?? 0, r.hard ?? 0];
        return (
          <Link
            key={r.leetcode_username}
            href={`/users/${slugify(r.leetcode_username)}/`}
            className={`rank-row${topClass}`}
          >
            <div className="rank-pos">#{pos}</div>
            <div className="rank-meta">
              <strong>{r.display_name}</strong>
              <span>
                @{r.leetcode_username} · {r.server_region} ·{" "}
                <span style={{ color: "var(--easy)" }}>{breakdown[0]}</span> /{" "}
                <span style={{ color: "var(--medium)" }}>{breakdown[1]}</span> /{" "}
                <span style={{ color: "var(--hard)" }}>{breakdown[2]}</span>
              </span>
            </div>
            <div className="rank-score">
              {r.total_solved ?? 0}
              <small>solved</small>
            </div>
          </Link>
        );
      })}
    </div>
  );
}

function BenchmarkTab({ benchmarks }: { benchmarks: Benchmarks }) {
  const [period, setPeriod] = useState<BenchmarkPeriod>("weekly");
  const rows: BenchmarkEntry[] = benchmarks[period];

  const label: Record<BenchmarkPeriod, string> = {
    daily: "Last 24 hours",
    weekly: "Last 7 days",
    monthly: "Last 30 days",
  };

  return (
    <div>
      <div className="subtabs" role="tablist" aria-label="Benchmark window">
        {(["daily", "weekly", "monthly"] as const).map((p) => (
          <button
            key={p}
            type="button"
            role="tab"
            aria-selected={period === p}
            className={period === p ? "active" : ""}
            onClick={() => setPeriod(p)}
          >
            {p[0]!.toUpperCase() + p.slice(1)}
          </button>
        ))}
      </div>
      <p className="muted" style={{ marginTop: 0, fontSize: "0.85rem" }}>
        AC submissions in the <strong>{label[period].toLowerCase()}</strong>,
        ranked per member. Counts come from each member&apos;s recent AC feed at
        the last collector run.
      </p>
      {rows.length === 0 ? (
        <div className="empty">No data for this window.</div>
      ) : (
        <div className="rank-list">
          {rows.map((r, i) => {
            const pos = i + 1;
            const topClass =
              r.count > 0 && pos <= 3 ? ` top-${pos}` : "";
            return (
              <Link
                key={r.leetcode_username}
                href={`/users/${slugify(r.leetcode_username)}/`}
                className={`rank-row${topClass}`}
              >
                <div className="rank-pos">#{pos}</div>
                <div className="rank-meta">
                  <strong>{r.display_name}</strong>
                  <span>
                    @{r.leetcode_username} · {r.server_region}
                  </span>
                </div>
                <div className="rank-score">
                  {r.count}
                  <small>AC</small>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function MainTabs({ members, leaderboard, benchmarks }: Props) {
  const [tab, setTab] = useState<TabKey>("leaderboard");
  return (
    <>
      <div className="tabs" role="tablist" aria-label="Main view">
        <button
          role="tab"
          aria-selected={tab === "leaderboard"}
          className={tab === "leaderboard" ? "active" : ""}
          onClick={() => setTab("leaderboard")}
        >
          Leaderboard
        </button>
        <button
          role="tab"
          aria-selected={tab === "roster"}
          className={tab === "roster" ? "active" : ""}
          onClick={() => setTab("roster")}
        >
          Roster
        </button>
        <button
          role="tab"
          aria-selected={tab === "benchmarks"}
          className={tab === "benchmarks" ? "active" : ""}
          onClick={() => setTab("benchmarks")}
        >
          Benchmarks
        </button>
      </div>

      {tab === "leaderboard" && <LeaderboardTab rows={leaderboard} />}
      {tab === "roster" && <RosterTab members={members} />}
      {tab === "benchmarks" && <BenchmarkTab benchmarks={benchmarks} />}
    </>
  );
}
