# Changelog

## 0.1.0-rc.3

- Add native Home Assistant OS app icon and logo.
- Align HAOS and collector version metadata.
- No collector behavior changes.
- HAOS runtime validation remains pending.

## 0.1.0-rc.2
- Monotonic polling schedule; MQTT events no longer trigger early hardware scans.
- Five-second retry after scan or publication failure and grace for an isolated scan failure.
- Five additional bridge diagnostics; no replay of stale adapter samples.
- Scheduler and failure-policy unit tests, project logo and upgrade/rollback guidance.
- Runtime and HAOS validation remain pending.

## 0.1.0-rc.1
- Refresh discovery on Home Assistant birth messages.
- Add MQTT discovery origin metadata.
- Avoid rewriting unchanged adapter cache.
- Experimental HAOS source-build app and CI builds.
- Release validation checklist.

## 0.1.0-alpha.3
- Cache discovery payloads; refresh on MQTT reconnection or poll failure.
- Require two successful missing-adapter observations before marking it offline.
- Recover from corrupt persisted adapter cache.
- Add runtime regression tests and non-publishing multi-platform build checks.
- Improve README navigation and compatibility guidance.

## 0.1.0-alpha.2
- Stable alpha.1 MQTT identities with manufacturer hints, icons and diagnostic metadata.
- Adapter connectivity binary sensors and five bridge diagnostics.
- Initial scan retry after five seconds; additional discovery regression tests.
- Documentation and gated multi-platform container publishing workflow.

## 0.1.0-alpha.1
- Initial collector, Docker Compose, topology parser and MQTT discovery.
- Validated on Raspberry Pi 5 with three adapters and 18 Home Assistant sensors.
