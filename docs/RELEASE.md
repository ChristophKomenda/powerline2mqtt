# v0.1.0 release gates

Record actual results and dates; do not mark tests as passed based on CI configuration alone.

- [ ] All CI jobs pass for the exact release commit (both architectures, both images).
- [ ] Docker live test on ARM64: three known adapters, existing entity IDs preserved, bridge diagnostics present.
- [ ] Stop/restart collector: availability recovers; no duplicate entities.
- [ ] Disconnect/reconnect one remote adapter (not the local uplink): offline after two successful missing observations; online on return.
- [ ] Restart Home Assistant: birth message triggers fresh discovery and readings at the next scheduled successful scan, without an early hardware scan.
- [ ] Test broker outage in isolated test broker, then reconnect; no impact on production services.
- [ ] HAOS clean install, options, startup, restart, discovery, upgrade and removal on supported architectures; document actual results.
- [ ] AMD64 runtime smoke test; record hardware and versions.
- [ ] Review Debian copyright files for every redistributed package and base image, document applicable notices/source obligations and fulfill them before GHCR publication. Keep workflow gated otherwise.
- [ ] Review README, screenshots (redact identifying data), security and upgrade/rollback guidance.
- [ ] Bump both Python version files and HAOS config to 0.1.0, update changelogs, verify tests and tag exact merged commit.

If a gate fails, publish only an explicitly labeled prerelease; do not claim unsupported hardware or stable HAOS support.

## Recorded evidence (25 November 2026)

RC.1 on Raspberry Pi 5 / Debian 13 / ARM64: 14 unit tests passed; three adapters detected; Python process RSS 23,024 KiB. Collector restarted and recovered after one transient missing-local-adapter scan. Four of five logged scans succeeded; this is a short observation, not a stability benchmark. CI on the RC.1 main merge was green. These observations do not satisfy RC.2 runtime gates.

## RC.2 focused regression checks

- [ ] Verify five new bridge diagnostics and unchanged existing MQTT entity IDs (31 expected entities if the same 26 RC.1 entities exist).
- [ ] Verify regular scan cadence and that HA birth events do not trigger immediate scans.
- [ ] Verify first transient scan failure retains healthy availability when appropriate; repeat failure marks bridge unavailable; recovery follows a successful retry.
- [ ] Verify no stale adapter measurements are republished on a failed scan.
- [ ] Verify hardware failure counters exclude MQTT publication errors.
