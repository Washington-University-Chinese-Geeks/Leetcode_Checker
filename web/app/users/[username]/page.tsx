import Link from "next/link";
import { notFound } from "next/navigation";

import { listUserSlugs, loadUserBySlug } from "../../../lib/data";

type Params = { username: string };

export function generateStaticParams(): Params[] {
  return listUserSlugs().map((username) => ({ username }));
}

function formatTimestamp(unixSeconds: string, iso?: string): string {
  if (iso) return new Date(iso).toISOString().replace("T", " ").slice(0, 16) + "Z";
  const n = Number(unixSeconds);
  if (!n) return "";
  return new Date(n * 1000).toISOString().replace("T", " ").slice(0, 16) + "Z";
}

export default function UserPage({ params }: { params: Params }) {
  const user = loadUserBySlug(params.username);
  if (!user) notFound();

  return (
    <>
      <Link href="/" className="back-link">
        ← back to roster
      </Link>
      <h1>
        {user.display_name}{" "}
        <small>
          @{user.leetcode_username} · {user.server_region}
        </small>
      </h1>

      {user.totals && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3>Totals</h3>
          <div className="stat">
            <span>Easy</span>
            <span>{user.totals.easy ?? "—"}</span>
          </div>
          <div className="stat">
            <span>Medium</span>
            <span>{user.totals.medium ?? "—"}</span>
          </div>
          <div className="stat">
            <span>Hard</span>
            <span>{user.totals.hard ?? "—"}</span>
          </div>
          <div className="stat">
            <span>All</span>
            <span>{user.totals.all ?? "—"}</span>
          </div>
        </div>
      )}

      <h3>Recent accepted submissions</h3>
      {user.recent_submissions.length === 0 ? (
        <p className="muted">No recent AC submissions recorded.</p>
      ) : (
        <ul className="submission-list">
          {user.recent_submissions.map((s) => (
            <li key={s.id}>
              <a
                href={
                  s.proof_url ?? `https://leetcode.com/problems/${s.title_slug}/`
                }
                target="_blank"
                rel="noreferrer"
              >
                {s.title}
              </a>
              <time>{formatTimestamp(s.timestamp, s.submitted_at)}</time>
            </li>
          ))}
        </ul>
      )}

      <p className="muted" style={{ marginTop: "2rem" }}>
        Last updated {new Date(user.last_updated).toISOString().slice(0, 19)}Z
      </p>
    </>
  );
}
