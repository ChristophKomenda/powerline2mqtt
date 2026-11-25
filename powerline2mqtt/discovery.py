"""Pure discovery payload builders; stable alpha.1 identifiers."""
from . import __version__

ORIGIN = {'name': 'Powerline2MQTT', 'sw_version': __version__, 'support_url': 'https://github.com/ChristophKomenda/powerline2mqtt'}

VENDORS = {'34:E8:94': 'TP-Link', '80:CA:4B': 'Gongjin Electronics'}

def adapter_configs(row, node, prefix, interval):
    mac = row['mac']
    key = mac.replace(':', '').lower()
    ident = f'powerline2mqtt_{node}_{key}'
    base = f'powerline2mqtt/{node}'
    root = f'{base}/{key}'
    vendor = VENDORS.get(mac[:8])
    device = {'identifiers': [ident], 'name': f'{vendor or "Powerline"} {mac[-8:]} ({node})'}
    if vendor: device['manufacturer'] = vendor
    if row['chipset']: device['model'] = row['chipset']
    if row['firmware']: device['sw_version'] = row['firmware']
    fields = {'role': ('Network role','mdi:network'), 'locality': ('Location','mdi:lan'), 'tei': ('TEI','mdi:identifier'), 'mac': ('MAC address','mdi:identifier'), 'chipset': ('Chipset','mdi:chip'), 'firmware': ('Firmware','mdi:package-variant')}
    if row['locality'] == 'REM': fields.update(tx=('TX link rate','mdi:upload-network'), rx=('RX link rate','mdi:download-network'))
    availability = [{'topic': f'{base}/availability'}, {'topic': f'{root}/availability'}]
    for field, (name, icon) in fields.items():
        if row[field] is None and field in ('chipset','firmware'): continue
        cfg = dict(name=name, unique_id=f'{ident}_{field}', device=device, icon=icon, state_topic=f'{root}/state', value_template='{{ value_json.'+field+' }}', availability=availability, availability_mode='all', expire_after=interval*3)
        if field in ('tx','rx'):
            cfg.update(unit_of_measurement='Mbit/s', device_class='data_rate', state_class='measurement')
        else: cfg['entity_category']='diagnostic'
        cfg['origin'] = ORIGIN
        yield f'{prefix}/sensor/{ident}/{field}/config', cfg
    # Bridge outage makes connectivity unknown, not falsely disconnected.
    yield f'{prefix}/binary_sensor/{ident}/connectivity/config', dict(origin=ORIGIN, name='Connectivity', unique_id=f'{ident}_connectivity', device=device, device_class='connectivity', state_topic=f'{root}/availability', payload_on='online', payload_off='offline', availability_topic=f'{base}/availability', entity_category='diagnostic')

def bridge_configs(node, prefix, interval):
    ident=f'powerline2mqtt_{node}_bridge'
    base=f'powerline2mqtt/{node}'
    device=dict(identifiers=[ident], name=f'Powerline2MQTT Bridge ({node})', manufacturer='Powerline2MQTT')
    for field,name,icon in [('count','Detected adapters','mdi:network'),('failures','Failed polls (session)','mdi:alert-circle-outline'),('last_success','Last successful poll','mdi:clock-outline'),('interface','Network interface','mdi:lan'),('version','Version','mdi:package-variant'),('successes','Successful polls (session)','mdi:check-circle-outline'),('consecutive_failures','Consecutive failed polls','mdi:alert-outline'),('success_rate','Poll success rate','mdi:percent'),('poll_interval','Polling interval','mdi:timer-outline'),('retry_interval','Retry interval','mdi:timer-refresh-outline')]:
        cfg=dict(name=name, unique_id=f'{ident}_{field}', device=device, icon=icon, state_topic=f'{base}/bridge/state', value_template='{{ value_json.'+field+' }}', availability_topic=f'{base}/availability', entity_category='diagnostic', expire_after=interval*3)
        if field=='last_success': cfg['device_class']='timestamp'
        if field in ('count','success_rate','consecutive_failures'): cfg['state_class']='measurement'
        if field=='success_rate': cfg['unit_of_measurement']='%'
        if field in ('poll_interval','retry_interval'): cfg.update(device_class='duration', unit_of_measurement='s')
        cfg['origin'] = ORIGIN
        yield f'{prefix}/sensor/{ident}/{field}/config', cfg
