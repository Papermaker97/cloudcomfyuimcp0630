# Cloud ComfyUI MCP

Client configuration for connecting AI agents (Claude Code, Claude Desktop) to
[Comfy Cloud's](https://cloud.comfy.org) hosted MCP server, as announced in
[Comfy MCP: Turn your agent into a creative technologist](https://blog.comfy.org/p/comfy-mcp-turn-your-agent-into-a).

Comfy Cloud exposes the full ComfyUI engine — image, video, 3D, and audio
generation models, plus hundreds of community workflows — as MCP tools. Once
connected, an agent can search models/nodes/templates and run ComfyUI
workflows entirely in natural language, with no local GPU or node graph
required.

This repo does not run any server itself; it only holds the connector config
and setup notes for pointing an MCP client at the Comfy Cloud endpoint.

## Prerequisites

- A [Comfy Cloud](https://cloud.comfy.org) account (currently closed beta —
  join the waitlist if you don't have access yet).
- Claude Code or Claude Desktop (the only clients Comfy Cloud MCP officially
  supports today; both authenticate via a one-time OAuth browser sign-in).

## Setup: Claude Code

This repo already includes a project-scoped [`.mcp.json`](./.mcp.json)
pointing at `https://cloud.comfy.org/mcp`. From this directory:

```
claude
/mcp
```

Select `comfy-cloud` from the list and choose **Authenticate** to complete
the OAuth sign-in. After that, Comfy's tools (generate image/video/audio/3D,
search models/nodes/templates, run workflows) are available in the session.

## Setup: Claude Desktop

1. Open **Settings → Connectors → Add custom connector**.
2. Set the URL to `https://cloud.comfy.org/mcp`.
3. Save, then sign in when prompted.

## Workflows

- [`workflows/`](./workflows/) — ready-to-run workflows built against this
  connector. Currently: a Seedance 2.0 multi-scene lip-sync workflow that
  shares one song + character sheet across scenes and varies only the audio
  cut, key visual, lyrics, and staging prompt.

## Reference

- [Comfy MCP announcement](https://blog.comfy.org/p/comfy-mcp-turn-your-agent-into-a)
- [Comfy Cloud MCP docs](https://docs.comfy.org/development/cloud/mcp-server)
