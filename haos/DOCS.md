# Experimental Home Assistant OS app

Add `https://github.com/ChristophKomenda/powerline2mqtt` as an app repository, install the experimental app, and configure the MQTT broker address, credentials and physical Ethernet interface. The broker must be reachable from the host. A dedicated node ID avoids conflicts with other collectors. Start manually and inspect logs. MQTT discovery must be enabled in Home Assistant.

This source-build app is not yet validated on HAOS. Host networking and NET_RAW are needed for Layer 2 queries. No privileged container or device reset is intended. Do not disable protection mode merely to bypass errors; report them. TLS uses system trust; custom CA configuration is not exposed in this app yet. Stop the app before starting another collector with the same node ID.

## FRITZ!Box backend

Experimental configuration options:

- powerline_backend: homeplug or fritzbox
- fritzbox_url: FRITZ!Box TR-064 URL
- fritzbox_username: FRITZ!Box account
- fritzbox_password: FRITZ!Box account password
- fritzbox_reference_mac: reference Powerline adapter

HomePlug remains the default backend.
HAOS runtime validation is pending.
