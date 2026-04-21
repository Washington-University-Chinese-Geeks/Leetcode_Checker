import MainTabs from "./components/MainTabs";
import { loadAllUsers, loadBenchmarks, loadSummary } from "../lib/data";

function formatDate(iso: string): string {
  if (!iso) return "never";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime()) || d.getTime() === 0) return "never";
  return d.toISOString().slice(0, 10);
}

export default function HomePage() {
  const summary = loadSummary();
  const users = loadAllUsers();
  const benchmarks = loadBenchmarks(users);

  const userByName = new Map(users.map((u) => [u.leetcode_username, u]));
  const leaderboard = summary.members.map((m) => {
    const u = userByName.get(m.leetcode_username);
    return {
      leetcode_username: m.leetcode_username,
      display_name: m.display_name,
      server_region: m.server_region,
      total_solved: m.total_solved ?? u?.totals?.all ?? null,
      easy: u?.totals?.easy ?? null,
      medium: u?.totals?.medium ?? null,
      hard: u?.totals?.hard ?? null,
    };
  });

  return (
    <>
      <h1>
        WUCG LeetCode{" "}
        <small>
          {summary.member_count} members · updated {formatDate(summary.generated_at)}
        </small>
      </h1>
      <MainTabs
        members={summary.members}
        leaderboard={leaderboard}
        benchmarks={benchmarks}
      />
    </>
  );
}
