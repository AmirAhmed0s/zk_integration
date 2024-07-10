from __future__ import unicode_literals
from dateutil.parser import parse
import frappe
from frappe import _
import requests
import json




TIMEOUT = 600

PAGE_SIZE = 50


def get_bio_settings():
    bio_settings = frappe.get_single("BioTime Settings")
    if not (bio_settings and bio_settings.url and bio_settings.user and bio_settings.pwd):
        frappe.throw(_("Please set BioTime Settings First"))

    return get_bio_token(
        bio_settings.url, bio_settings.user, bio_settings.pwd)


def get_bio_token(url, user, pwd , timeout = 600 , page_size = 200 ):
    method = "/jwt-api-token-auth/"

    method_url = url + method

    json = {
        "username": user,
        "password": pwd
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(method_url, headers=headers, json=json,timeout=timeout or TIMEOUT)
    json_response = {}
    token = None
    try:
        json_response = response.json()
    except:
        pass
    # frappe.msgprint(str(json_response))
    if response.status_code == 200:
        token = json_response.get("token")
    else:
        frappe.msgprint(str(json_response.get("non_field_errors")))
        frappe.throw(
            _("Invalid BioTime Login Please Check BioTime Settings or BioTime Server"))

    if not token:
        frappe.throw(_("Invalid BioTime Login Please Check BioTime Settings"))

    return frappe._dict({
        "user": user,
        "pwd": pwd,
        "url": url,
        "timeout": timeout,
        "page_size": page_size,
        "url": url,
        "token": token
    })


def get_devices_data():
    biotime_data = get_bio_settings()
    method = "/iclock/api/terminals/"
    data = []
    method_url = biotime_data.url + method

    json = {
    }
    params = {
        "page" : 1,
        "page_size" : biotime_data.page_size or PAGE_SIZE
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization" : f"JWT {biotime_data.token}"
    }
    response = requests.request(
        "GET",method_url, headers=headers, json=json , params=params,timeout=biotime_data.timeout or TIMEOUT)
    json_response = {}
    try:
        json_response = response.json()
    except:
        pass
    # frappe.msgprint(str(method_url))
    # frappe.msgprint(str(headers))
    # frappe.msgprint(str(json_response))
    if response.status_code == 200:
        data = json_response.get("data") or []
        next = json_response.get("next")
        if next:
            data.extend(fetch_next_data(method_url,headers,json,params) or [])

    return data


def get_device_transactions(serial=None , last_log = None , fetch_next = 1):
    biotime_data = get_bio_settings()
    method = "/iclock/api/transactions/"
    data = []
    method_url = biotime_data.url + method

    json = {
    }
    params = {
        "page" : 1,
        "page_size" : biotime_data.page_size or PAGE_SIZE
    }
    if serial :
        params ["terminal_sn"] = serial
    if last_log :
        params ["start_time"] = last_log
        
        
        
    headers = {
        "Content-Type": "application/json",
        "Authorization" : f"JWT {biotime_data.token}"
    }
    response = requests.request(
        "GET", method_url, headers=headers, json=json,params=params,timeout=biotime_data.timeout or TIMEOUT)
    json_response = {}
    try:
        json_response = response.json()
    except:
        pass
    # frappe.msgprint(str(params))
    # frappe.msgprint(str(json_response))
    if response.status_code == 200:
        data = json_response.get("data") or []
        next = json_response.get("next")
        if next and fetch_next:
            data.extend(fetch_next_data(method_url,headers,json,params) or [])

    return data



def fetch_next_data(method_url,headers,json={},params={}):
    data = []
    
    params ['page'] = (params.get("page") or 0) + 1 
    
    # frappe.msgprint(str(next))
    response = requests.request(
        "GET", method_url, headers=headers, json=json,params=params)
    json_response = {}
    try:
        json_response = response.json()
    except:
        pass
    
    if response.status_code == 1000:
        data = json_response.get("data") or []
        next_t = json_response.get("next")
        if next_t:
            data.extend(fetch_next_data(method_url,headers,json,params) or [])

    return data


