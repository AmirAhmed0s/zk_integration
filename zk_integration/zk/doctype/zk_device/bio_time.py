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
        bio_settings.url,
        bio_settings.user,
        bio_settings.pwd,
        timeout=bio_settings.timout,
        page_size=bio_settings.page_size,
    )


def get_bio_token(url, user, pwd, timeout=600, page_size=200):
    method = "/jwt-api-token-auth/"

    url = url.rstrip("/")
    method_url = url + method

    payload = {
        "username": user,
        "password": pwd
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(method_url, headers=headers, json=payload, timeout=timeout or TIMEOUT)
    json_response = {}
    token = None
    try:
        json_response = response.json()
    except Exception:
        pass

    if response.status_code == 200:
        token = json_response.get("token")
    else:
        error_detail = json_response.get("non_field_errors") or json_response.get("detail") or str(json_response)
        frappe.msgprint(str(error_detail))
        frappe.throw(
            _("Invalid BioTime Login. Please check BioTime Settings or BioTime Server."))

    if not token:
        frappe.throw(_("Invalid BioTime Login. Please check BioTime Settings."))

    return frappe._dict({
        "user": user,
        "pwd": pwd,
        "url": url,
        "timeout": timeout or TIMEOUT,
        "page_size": page_size or PAGE_SIZE,
        "token": token
    })


@frappe.whitelist()
def test_bio_connection():
    """Test BioTime server connection using saved BioTime Settings."""
    bio_data = get_bio_settings()
    frappe.msgprint(_("Connected to BioTime successfully!"), indicator="green")


def get_devices_data():
    biotime_data = get_bio_settings()
    method = "/iclock/api/terminals/"
    data = []
    method_url = biotime_data.url + method

    params = {
        "page": 1,
        "page_size": biotime_data.page_size or PAGE_SIZE
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"JWT {biotime_data.token}"
    }
    response = requests.request(
        "GET", method_url, headers=headers, params=params,
        timeout=biotime_data.timeout or TIMEOUT)
    json_response = {}
    try:
        json_response = response.json()
    except Exception:
        pass

    if response.status_code == 200:
        data = json_response.get("data") or []
        next_url = json_response.get("next")
        if next_url:
            data.extend(fetch_next_data(method_url, headers, params=params) or [])
    else:
        error_detail = json_response.get("detail") or str(json_response)
        frappe.throw(
            _("BioTime API error fetching devices (HTTP {0}): {1}").format(
                response.status_code, error_detail))

    return data


def get_device_transactions(serial=None, last_log=None, fetch_next=1):
    biotime_data = get_bio_settings()
    method = "/iclock/api/transactions/"
    data = []
    method_url = biotime_data.url + method

    params = {
        "page": 1,
        "page_size": biotime_data.page_size or PAGE_SIZE
    }
    if serial:
        params["terminal_sn"] = serial
    if last_log:
        params["start_time"] = last_log

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"JWT {biotime_data.token}"
    }
    response = requests.request(
        "GET", method_url, headers=headers, params=params,
        timeout=biotime_data.timeout or TIMEOUT)
    json_response = {}
    try:
        json_response = response.json()
    except Exception:
        pass

    if response.status_code == 200:
        data = json_response.get("data") or []
        next_url = json_response.get("next")
        if next_url and fetch_next:
            data.extend(fetch_next_data(method_url, headers, params=params) or [])
    else:
        error_detail = json_response.get("detail") or str(json_response)
        frappe.throw(
            _("BioTime API error fetching transactions (HTTP {0}): {1}").format(
                response.status_code, error_detail))

    return data


def fetch_next_data(method_url, headers, params=None):
    if params is None:
        params = {}
    data = []

    params = dict(params)
    params["page"] = (params.get("page") or 0) + 1

    response = requests.request(
        "GET", method_url, headers=headers, params=params)
    json_response = {}
    try:
        json_response = response.json()
    except Exception:
        pass

    if response.status_code == 200:
        data = json_response.get("data") or []
        next_url = json_response.get("next")
        if next_url:
            data.extend(fetch_next_data(method_url, headers, params=params) or [])

    return data


