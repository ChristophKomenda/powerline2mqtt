# v0.1.0 release gates

Record actual results and dates; do not mark tests as passed based on CI configuration alone.

- [ ] All CI jobs pass for the exact release commit (both architectures, both images).
- [ ] Docker live test on ARM64: three known adapters, existing entity IDs preserved, bridge diagnostics present.
- [ ] Stop/restart collector: availability recovers; no duplicate entities.
- [ ] Disconnect/reconnect one remote adapter (not the local uplink): offline after two successful missing observations; online on return.
- [ ] Restart Home Assistant: birth message triggers fresh discovery and readings.
- [ ] Test broker outage in isolated test broker, then reconnect; no impact on production services.
- [ ] HAOS clean install, options, startup, restart, discovery, upgrade and removal on supported architectures; document actual results.
- [ ] AMD64 runtime smoke test; record hardware and versions.
- [ ] Review Debian copyright files for every redistributed package and base image, document applicable notices/source obligations and fulfill them before GHCR publication. Keep workflow gated otherwise.
- [ ] Review README, screenshots (redact identifying data), security and upgrade/rollback guidance.
- [ ] Bump both Python version files and HAOS config to 0.1.0, update changelogs, verify tests and tag exact merged commit.

If a gate fails, publish only an explicitly labeled prerelease; do not claim unsupported hardware or stable HAOS support.
