# OmniRoute — integration preparation

Status: **prepared, not installed or activated**. This document does not change runtime routing, Codex settings, GitHub Actions, or the default branch.

## Source and security

Official upstream: https://github.com/cheaper-inference/OmniRoute
Optional third-party agent skill: https://github.com/hongkongkiwi/omniroute-skill

Review the upstream release, install scripts, dependency permissions and the skill scripts before running them. The third-party skill is not part of the official gateway. Never commit credentials.

## Gateway installation on the Codex host

1. Ensure a supported Node.js/npm installation is available on the actual host running Codex.
2. Review the published package and its installation scripts, then install from the official npm package: `npm install -g omniroute`.
3. Run `omniroute --help` to inspect supported commands for the installed version. Follow the upstream Codex integration instructions for that version; do not assume a specific setup subcommand exists.
4. Start and configure the gateway following the upstream documentation. Configure at least one provider and store credentials outside Git.
5. Configure Codex to use the gateway only after reviewing existing local Codex settings and preserving a backup.

## Validation checklist

- [ ] Gateway command runs on the Codex host
- [ ] Gateway process starts and health check passes
- [ ] Provider is configured without committing secrets
- [ ] Codex can send a minimal request through the gateway
- [ ] Fallback tested using a safe test model/provider
- [ ] Optional third-party skill independently reviewed and installed if desired

No repository-side install can establish these local-host checks. Keep this branch unmerged until verification.
