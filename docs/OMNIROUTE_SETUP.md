# OmniRoute integration (proposed)

This repository is prepared for an optional OmniRoute AI gateway integration. No credentials or runtime routing are enabled by this document.

## Local prerequisites

- Install and run OmniRoute from its verified upstream distribution: https://github.com/UmeshOnAI/OmniRoute-AI-Gateway
- Connect a model provider in the OmniRoute dashboard and create a scoped endpoint API key.
- Keep API keys in your local secret manager or environment; never commit them to Git.
- Verify the gateway health endpoint before configuring any coding agents.

## Codex CLI

Run `omniroute setup-codex --dry-run` to preview the proposed local Codex configuration. After reviewing the changes, run `omniroute setup-codex` on the machine hosting Codex. A remote gateway can be selected with `--remote <url> --api-key <key>` (avoid storing keys in shell history).

## Optional coding-agent skill

The third-party OmniRoute agent skill is documented at https://github.com/hongkongkiwi/omniroute-skill. Review its SKILL.md and scripts before installing into `~/.agents/skills/omniroute`. It requires a running OmniRoute server and a suitably scoped key.

## Validation

1. Verify OmniRoute is running and a provider is connected.
2. Confirm the intended Codex profile is configured and can list models.
3. Send a minimal test request and verify routing and fallback behavior.
4. Ensure no credentials or local secrets are tracked by Git.

This integration is opt-in; it does not change application traffic, GitHub Actions, or the default branch.
