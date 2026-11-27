"""Read-only FRITZ!Box TR-064 Powerline backend."""

import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from .parser import MAC

HOMEPLUG = "urn:dslforum-org:service:X_AVM-DE_Homeplug:1"
HOSTS = "urn:dslforum-org:service:Hosts:1"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class FritzBoxClient:
    def __init__(self, base_url, username, password, timeout=15):
        self.base_url = base_url.rstrip("/")
        parsed = urllib.parse.urlsplit(self.base_url)

        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Invalid FRITZ!Box URL")

        self.timeout = timeout
        manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        manager.add_password(
            None, self.base_url, username, password
        )

        self.opener = urllib.request.build_opener(
            urllib.request.HTTPDigestAuthHandler(manager),
            urllib.request.ProxyHandler({}),
            NoRedirect(),
        )

    def soap(self, service, control, action, arguments=None):
        args = "".join(
            f"<{key}>{escape(str(value))}</{key}>"
            for key, value in (arguments or {}).items()
        )

        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<s:Envelope xmlns:s='
            '"http://schemas.xmlsoap.org/soap/envelope/">'
            '<s:Body>'
            f'<u:{action} xmlns:u="{service}">'
            f'{args}</u:{action}>'
            '</s:Body></s:Envelope>'
        )

        request = urllib.request.Request(
            self.base_url + control,
            data=body.encode(),
            headers={
                "Content-Type": 'text/xml; charset="utf-8"',
                "SOAPAction": f'"{service}#{action}"',
            },
        )

        with self.opener.open(
            request, timeout=self.timeout
        ) as response:
            root = ET.fromstring(response.read())

        result = root.find(".//{*}" + action + "Response")

        if result is None:
            raise ValueError("Invalid SOAP response")

        return {
            child.tag.split("}")[-1]: child.text
            for child in result
        }

    def devices(self):
        result = self.soap(
            HOMEPLUG,
            "/upnp/control/x_homeplug",
            "GetNumberOfDeviceEntries",
        )

        count = int(result["NewNumberOfEntries"])

        if not 0 <= count <= 256:
            raise ValueError("Invalid adapter count")

        return [
            self.soap(
                HOMEPLUG,
                "/upnp/control/x_homeplug",
                "GetGenericDeviceEntry",
                {"NewIndex": index},
            )
            for index in range(count)
        ]

    def mesh(self):
        result = self.soap(
            HOSTS,
            "/upnp/control/hosts",
            "X_AVM-DE_GetMeshListPath",
        )

        url = urllib.parse.urljoin(
            self.base_url + "/",
            result["NewX_AVM-DE_MeshListPath"],
        )

        target = urllib.parse.urlsplit(url)
        origin = urllib.parse.urlsplit(self.base_url)

        if (
            target.scheme != origin.scheme
            or target.netloc != origin.netloc
        ):
            raise ValueError("Unexpected mesh URL origin")

        with self.opener.open(
            url, timeout=self.timeout
        ) as response:
            return json.load(response)

    def poll(self, reference_mac):
        return parse_mesh(
            self.devices(), self.mesh(), reference_mac
        )


def normalize_mac(value):
    value = str(value or "").upper()
    return value if MAC.fullmatch(value) else None


def mbps(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and value >= 0:
        return value / 1000
    return None


def parse_mesh(devices, mesh, reference_mac):
    reference = normalize_mac(reference_mac)

    if not reference:
        raise ValueError("Invalid reference adapter MAC")

    active = {}

    for device in devices:
        mac = normalize_mac(device.get("NewMACAddress"))

        if mac and str(device.get("NewActive")) == "1":
            active[mac] = device

    nodes = mesh.get("nodes")

    if not isinstance(nodes, list):
        raise ValueError("Invalid mesh nodes")

    rows = {}
    node_macs = {}
    links = {}

    for node in nodes:
        mac = normalize_mac(node.get("device_mac_address"))

        if mac not in active:
            continue

        node_macs[node["uid"]] = mac

        rows[mac] = {
            "mac": mac,
            "locality": "LOC" if mac == reference else "REM",
            "role": None,
            "tei": None,
            "bda": None,
            "tx": None,
            "rx": None,
            "chipset": None,
            "firmware": (
                node.get("device_firmware_version") or None
            ),
        }

        for interface in node.get("node_interfaces", []):
            if interface.get("type") != "PLC":
                continue

            for link in interface.get("node_links", []):
                if (
                    link.get("type") == "PLC"
                    and link.get("state") == "CONNECTED"
                    and link.get("uid")
                ):
                    links.setdefault(link["uid"], link)

    if reference not in rows:
        raise ValueError("Reference adapter not available")

    if set(active) != set(rows):
        raise ValueError("Incomplete Powerline mesh topology")

    for link in links.values():
        first = node_macs.get(link.get("node_1_uid"))
        second = node_macs.get(link.get("node_2_uid"))

        if first == reference:
            remote = second
            tx = mbps(link.get("cur_data_rate_tx"))
            rx = mbps(link.get("cur_data_rate_rx"))
        elif second == reference:
            remote = first
            tx = mbps(link.get("cur_data_rate_rx"))
            rx = mbps(link.get("cur_data_rate_tx"))
        else:
            continue

        if remote in rows and remote != reference:
            rows[remote]["tx"] = tx
            rows[remote]["rx"] = rx

    return rows
