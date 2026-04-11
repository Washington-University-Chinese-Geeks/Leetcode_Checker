/**
 * Next.js config for a fully-static export targeting GitHub Pages.
 *
 * `output: 'export'` writes a static site to `out/` at build time; the
 * deploy workflow uploads that directory as the Pages artifact.
 *
 * When deployed under `https://<user>.github.io/<repo>/`, GitHub Pages
 * serves the site from a sub-path. Set NEXT_PUBLIC_BASE_PATH in the
 * deploy workflow (e.g. "/Leetcode_Checker") so routes and asset URLs
 * resolve correctly.
 */
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true,
  basePath,
  assetPrefix: basePath || undefined,
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
};

export default nextConfig;
