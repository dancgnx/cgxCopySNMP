# cgxCopySNMP
Copy CGX SNMP configurations from one Element to the other(s)

WARNING: USE AT YOUR OWN RISK, there will be no support from CloudGenix

# Setup
* Install python3
* Install cloudgenix python sdk : pip3 install cloudgenix
* Install pyyaml : pip3 install pyyaml
* Setup authentication as listed below

# Authentication
cgxCopySNMP.py looks for the following for AUTH, in this order of precedence:

* --email or --password options on the command line.
* CLOUDGENIX_USER and CLOUDGENIX_PASSWORD values imported from cloudgenix_settings.py
* CLOUDGENIX_AUTH_TOKEN value imported from cloudgenix_settings.py
* X_AUTH_TOKEN environment variable
* AUTH_TOKEN environment variable
* Interactive prompt for user/pass (if one is set, or all other methods fail.)

# Usage

Notice that CloudGenix API calls a claimed ION an element.

Controller port have differnt names on different model. If the script sees that the source interface has the work "controller" in it, it will try all the combination of controller interface names, so you can copy SNMP configs from 2k to 3k or 7k and vice versa.

## Get existing configuration

```
bash$ python3 cgxCopySNMPpy --list --s_element "Dan 2k"
agents:
- description: null
  tags: null
  v2_config:
    community: public
    enabled: true
  v3_config:
    enabled: true
    users_access:
    - auth_phrase: null
      auth_type: sha
      enc_phrase: null
      enc_type: none
      engine_id: '323452345363435'
      security_level: auth
      user_name: u_snmp
    - auth_phrase: null
      auth_type: sha
      enc_phrase: null
      enc_type: aes
      engine_id: '3624356345643674567'
      security_level: private
      user_name: u_snmmp3
traps:
- description: null
  enabled: true
  server_ip: 10.0.123.1
  source_interface: controller 1
  tags: null
  v2_config:
    community: g235345345
  v3_config: null
  version: v2
- description: null
  enabled: true
  server_ip: 10.0.123.1
  source_interface: controller 1
  tags: null
  v2_config: null
  v3_config:
    user_access:
      auth_phrase: null
      auth_type: sha
      enc_phrase: null
      enc_type: none
      engine_id: '3423543534'
      security_level: auth
      user_name: u_snmp
  version: v3
```

Notice that the returned YAML file do not include the passwords. You will have to edit this file and replace the enc_phrase or auth_phrase with a password sorrounded with a quote or a double 

## Apply a YAML configuration file to a since element

```
bash$ python3 cgxCopySNMPpy --snmp_file config.yaml --t_element "Awil_Home_ION2000"
INFO:cgxCopySNMP:Working on Awil_Home_ION2000
INFO:cgxCopySNMP:----- Deleting existing SNMP configs for Awil_Home_ION2000
INFO:cgxCopySNMP:----- Applying SNMP configs for Awil_Home_ION2000
```

notice that a YAML config file needs to be specified, together with a taarget element

## Apply a YAML configuration file to a many elements
```
bash$ python3 cgxCopySNMPpy --snmp_file config.yaml --element_file t_list.csv 
INFO:cgxCopySNMP:Working on Dan 2k
INFO:cgxCopySNMP:----- Deleting existing SNMP configs for None
INFO:cgxCopySNMP:----- Applying SNMP configs for None
INFO:cgxCopySNMP:Working on Awil_Home_ION2000
INFO:cgxCopySNMP:----- Deleting existing SNMP configs for None
INFO:cgxCopySNMP:----- Applying SNMP configs for None
```

the "element_file" is a file with a list of all target elements, one element name per line