# Changelog

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
