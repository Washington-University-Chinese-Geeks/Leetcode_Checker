import Link from "next/link";

import { loadSummary } from "../lib/data";

function formatDate(iso: string): string {
  if (!iso) return "never";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime()) || d.getTime() === 0) return "never";
  return d.toISOString().slice(0, 10);
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

export default function HomePage() {
  const summary = loadSummary();
  const members = [...summary.members].sort((a, b) =>
    (b.total_solved ?? 0) - (a.total_solved ?? 0),
  );

  return (
    <>
      <h1>
        Roster{" "}
        <small>
          {summary.member_count} members · updated {formatDate(summary.generated_at)}
        </small>
      </h1>

      {members.length === 0 && (
        <p>
          No member data yet. The collector workflow populates
          <code> data/summary.json</code> on its first successful run.
        </p>
      )}

      <div className="member-grid">
        {members.map((m) => (
          <Link
            key={m.leetcode_username}
            href={`/users/${slugify(m.leetcode_username)}/`}
            className="card"
          >
            <h3>{m.display_name}</h3>
            <div className="muted">
              {m.leetcode_username} · {m.server_region}
            </div>
            <div className="stat">
              <span>Total solved</span>
              <span>{m.total_solved ?? "—"}</span>
            </div>
            <div className="stat">
              <span>Recent AC</span>
              <span>{m.recent_submission_count ?? 0}</span>
            </div>
            <div className="stat">
              <span>Last AC</span>
              <span>{formatDate(m.last_submission_at ?? "")}</span>
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}
