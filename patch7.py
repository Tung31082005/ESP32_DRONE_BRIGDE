# -*- coding: utf-8 -*-
# Patch db_serial.c
with open('main/db_serial.c', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('return uart_driver_install(UART_NUM, 1024, 0, 10, NULL, 0);', 'return uart_driver_install(UART_NUM, 2048, 2048, 10, NULL, 0);')

with open('main/db_serial.c', 'w', encoding='utf-8') as f:
    f.write(c)

# Patch main.c
with open('main/main.c', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''        start_mdns_service();
        netbiosns_init();
        netbiosns_set_name("dronebridge");'''
replacement = '''        // [OPTIMIZATION] Disabled mDNS and NetBIOS to save RAM and reduce Wi-Fi broadcast noise
        // start_mdns_service();
        // netbiosns_init();
        // netbiosns_set_name("dronebridge");'''
c = c.replace(target, replacement)

with open('main/main.c', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
