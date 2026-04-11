import Link from "next/link";

export default function NotFound() {
  return (
    <>
      <h1>Not found</h1>
      <p>That page doesn't exist in the current data snapshot.</p>
      <Link href="/">← back to roster</Link>
    </>
  );
}
