#!/usr/bin/env python3

import cloudgenix
from cloudgenix import jd, jd_detailed
import cgxinit
import sys
import logging
import csv
import yaml


def getInterfaceByName(cgx,site,element,ifName):
    interfaces = cgx.get.interfaces(site,element).cgx_content["items"]
    int_json = None
    for interface in interfaces:
        if interface["name"] == ifName:
            return interface

    return int_json
def getInterfaceNameByID(site,element,interface):
    interface = cgx.get.interfaces(site,element,interface)
    if not interface:
        return None 
    else:
        return interface.cgx_content["name"]

def getElementByName(cgx,name):
    """
    get Element json object by using the element name
    """
    res = cgx.get.elements()
    if not res.cgx_status:
        print(res.cgx_content)
        raise ValueError(f"Can't retrieve element {name}")
    for item in res.cgx_content["items"]:
        if item["name"] == name:
            return item
    return None

def getSNMPAgentsByElementID(cgx,site_id,element_id,omit_id=False):
    """
    get the existing snmpagent config for an element ID
    """

    res = cgx.get.snmpagents(site_id=site_id,element_id=element_id)
    if not res.cgx_status:
        print(res.cgx_content)
        raise ValueError(f"Can't retrieve element snmpagent")
    
    # remove all _properties
    agents = res.cgx_content["items"]
    for agent in agents:
        del_keys = [
            key for key in agent if key.startswith("_") or (omit_id and key == "id")
        ]
        for key in del_keys:
            del(agent[key])
    return agents


def getSNMPTrapsByElementID(cgx,site_id,element_id,omit_id=False):
    """
    get the existing snmptraps config for an element ID
    """

    res = cgx.get.snmptraps(site_id=site_id,element_id=element_id)
    if not res.cgx_status:
        print(res.cgx_content)
        raise ValueError(f"Can't retrieve element snmptraps")
    # remove all _properties and translte interface names
    traps = res.cgx_content["items"]
    for trap in traps:
        del_keys = [
            key for key in trap if key.startswith("_") or (omit_id and key == "id")
        ]
        trap["source_interface"] = getInterfaceNameByID(site_id,element_id,trap["source_interface"])
        for key in del_keys:
            del(trap[key])
    return traps
def deleteSNMPConfig(cgx,site,element):
    # delete agents
    snmpagents = getSNMPAgentsByElementID(cgx,site,element)
    for agent in snmpagents:
        res = cgx.delete.snmpagents(site,element,agent["id"])
        if not res:
            print(f"Failed to delete SNMP agent for {agent['id']}")
    # delete traps
    snmptraps = getSNMPTrapsByElementID(cgx,site,element)
    for trap in snmptraps:
        res = cgx.delete.snmptraps(site,element,trap["id"])
        if not res:
            print(f"Failed to delete SNMP config for {element} ")
            sys.exit(-1)
def applySNMPConfig(cgx,site,element,snmp):
    for agent in snmp["agents"]:
        res = cgx.post.snmpagents(site,element,agent)
        if not res:
            jd_detailed(res)
            print(f"Can't create SNMP Agent config")
            sys.exit(-1)

    for trap in snmp["traps"]:
        #convert interface into import ip, if its a controller port, try diffrerent combinations
        if "controller" in trap["source_interface"]:
            s_interface = getInterfaceByName(cgx,site,element,"controller")
            if not s_interface:
                s_interface = getInterfaceByName(cgx,site,element,"controller 1")
        else:
            s_interface = getInterfaceByName(cgx,site,element,trap["source_interface"])
        if not s_interface:
            print(f"Can't find interface {trap['source_interface']} in target element")
            sys.exit(-1)
        save_interface=trap['source_interface']
        trap['source_interface'] = s_interface["id"]
        res = cgx.post.snmptraps(site,element,trap)
        if not res:
            jd_detailed(res)
            print(f"Can't create SNMP Traps config")
            sys.exit(-1)
        trap['source_interface'] = save_interface

if __name__ == "__main__":
    # initiate cgx objext and get ommand line arguments
    cgx, args = cgxinit.go()

    #init logging
    logging.basicConfig(level=logging.INFO)
    log=logging.getLogger("cgxCopySNMP")

    
    if args["list"] and args["s_element"]:
        #parse arguments
        s_element = getElementByName(cgx,args["s_element"])
        if not s_element:
            log.error(f"Couldn't find source element {args['s_element']}")
            sys.exit(-1)
        s_eid = s_element["id"]
        s_siteid = s_element["site_id"]
        # get existing device SNMP params
        snmpagents = getSNMPAgentsByElementID(cgx,s_siteid,s_eid,omit_id=True)
        snmptraps = getSNMPTrapsByElementID(cgx,s_siteid,s_eid,omit_id=True)
        snmp = {
            "agents" : snmpagents,
            "traps" : snmptraps
        }
        print(yaml.dump(snmp,default_flow_style = False))
    elif args["t_element"] and args["snmp_file"]:
        log.info(f"Working on {args['t_element']}")
        #parse arguments
        t_element = getElementByName(cgx,args["t_element"])
        if not t_element:
            log.error(f"Couldn't find target element {args['t_element']}")
            sys.exit(-1)
        t_eid = t_element["id"]
        t_siteid = t_element["site_id"]
        # load the config
        snmp = yaml.safe_load(args['snmp_file'])
        # delete existing config
        log.info(f"----- Deleting existing SNMP configs for {args['t_element']}")
        deleteSNMPConfig(cgx,t_siteid,t_eid)
        log.info(f"----- Applying SNMP configs for {args['t_element']}")
        applySNMPConfig(cgx,t_siteid,t_eid,snmp)

    elif args["elements_file"] and args["snmp_file"]:
        # load the config
        snmp = yaml.load(args['snmp_file'])
        # read targets from file
        elements_names= [
            line.strip() for line in args["elements_file"].readlines()
        ] 
        # for each element check if its in the element list
        elements = cgx.get.elements().cgx_content["items"]
        for t_element in elements:
            if t_element["name"] in elements_names:
                log.info(f"Working on {t_element['name']}")
                t_eid = t_element["id"]
                t_siteid = t_element["site_id"]
                # delete existing config
                log.info(f"----- Deleting existing SNMP configs for {args['t_element']}")
                deleteSNMPConfig(cgx,t_siteid,t_eid)
                log.info(f"----- Applying SNMP configs for {args['t_element']}")
                applySNMPConfig(cgx,t_siteid,t_eid,snmp)

