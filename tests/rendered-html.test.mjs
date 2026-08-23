import assert from "node:assert/strict";
import test from "node:test";

test("renders the HeatOps decision dashboard", async () => {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  const response = await worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );

  assert.equal(response.status, 200);
  assert.match(
    response.headers.get("content-type") ?? "",
    /^text\/html\b/i,
  );
  const html = await response.text();
  assert.match(html, /<title>HeatOps Decision Dashboard<\/title>/i);
  assert.match(html, /Run placement analysis/i);
  assert.match(html, /Optimized risk coverage/i);
  assert.match(html, /Synthetic data/i);
  assert.match(html, /Operational action brief/i);
  assert.match(html, /Download \.md/i);
});
