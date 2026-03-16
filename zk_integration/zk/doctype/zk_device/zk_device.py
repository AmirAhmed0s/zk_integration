# -*- coding: utf-8 -*-
# Copyright (c) 2021, Peter and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from zk import ZK, const
from datetime import datetime, date, timedelta, time
from frappe.utils import to_timedelta
import json
# from zk.doctype.device_log.device_log import create_employee_checkin
# from zk_integration.zk.doctype.device_log.device_log import create_employee_checkin
from frappe.utils.data import DATE_FORMAT, TIME_FORMAT
from dateutil import parser
from zk_integration.zk.doctype.zk_device.bio_time import get_device_transactions, get_devices_data
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ZKDevice(Document):

	@frappe.whitelist()
	def get_device_log(self, show_progress=False , fetch_next = False):
		if self.get_data_type == "Direct":
			self.get_device_logs_direct(show_progress)
		if self.get_data_type == "BioTime":
			self.get_device_logs_biotime(show_progress,fetch_next)

	@frappe.whitelist()
	def get_device_logs_direct (self, show_progress=False):
		conn = None
		zk = ZK(self.ip, port=self.port, password=self.password, timeout=20,
				force_udp=self.udp or True, ommit_ping=self.ping or True)
		# zk = ZK('192.168.1.201', port=4370, timeout=20 , ommit_ping=False)
		# if True:
		try:
			conn = zk.connect()
			# conn.disable_device()
			logs = conn.get_attendance() or []

			last_log_users = {}
			period = self.period or 0
			count = 1
			total = len(logs)
			if not total:
				frappe.throw(_("Empty Logs"))
			if self.last_log_row:
				self.last_log_row = parser.parse(str(self.last_log_row))
				# self.last_log_row = datetime.strptime(str(self.last_log_row),DATETIME_FORMAT)
			last = self.last_log_row
			for log in logs:
				if show_progress:
					frappe.publish_progress(
						count * 100 / total, title=_("Getting Logs..."))
				count += 1
				if self.last_log_row and (log.timestamp < self.last_log_row):
					continue
				last_timestamp = last_log_users.get(log.user_id) or None
				if period and last_timestamp:
					diff = (log.timestamp - last_timestamp).seconds / 3600
					if diff < period:
						continue

				try:
					# if True:
					# frappe.msgprint(str(log))
					log.status = 'IN' if log.status == 1 else 'OUT'

					# log.status = log.status.upper()
					name = "{}-{}-{}".format(log.user_id,
												log.timestamp, log.status)
					frappe.db.sql("""
					INSERT IGNORE INTO `tabDevice Log`
					(name, employee, enroll_no, time, date, type, punch,
					 creation, modified, owner, device)
					VALUES
					(%s,
					 (SELECT name FROM tabEmployee WHERE attendance_device_id = %s LIMIT 1),
					 %s, %s, %s, %s, %s,
					 CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), %s, %s)
					""", (name, log.user_id, log.user_id, log.timestamp,
						  log.timestamp.date(), log.status, log.punch,
						  frappe.session.user, self.name))
					last_log_users[log.user_id] = parser.parse(
						str(log.timestamp))
					# last_log_users [log.user_id] = datetime.strptime(str(log.timestamp),DATETIME_FORMAT)
				except:
					pass
				last = log.timestamp
			if last:
				self.last_log_row = min(last, datetime.now())

			frappe.db.commit()
			# conn.test_voice()
			conn.enable_device()

		except Exception as e:
			frappe.msgprint(
				_("Process terminate : {}".format(e)), indicator='red')
			self.last_connection_error = str(e)
		finally:
			self.last_connection_time = datetime.now()
			if conn:
				conn.enable_device()

				conn.disconnect()
		self.get_after_mins = self.get_after_mins or 5
		self.excecution_time = datetime.now() + timedelta(minutes=self.get_after_mins)

		self.save()
		sync_employee()


	@frappe.whitelist()
	def get_device_logs_biotime (self, show_progress=False , fetch_next = False):
		try:
			if not self.serial_no :
				frappe.throw(_("Device Serial is Empty"))
			if self.last_log_row:
				self.last_log_row = parser.parse(str(self.last_log_row))
    
			logs = get_device_transactions(serial=self.serial_no , last_log = self.last_log_row , fetch_next=fetch_next) or []
			period = self.period or 0
			count = 1
			total = len(logs)
			if not total:
				frappe.throw(_("Empty Logs"))
			last = self.last_log_row
			last_log_users = {}
			for log in logs:
				log = frappe._dict(log)
				if show_progress:
					frappe.publish_progress(
						count * 100 / total, title=_("Getting Logs..."))
				count += 1
				log.timestamp = parser.parse(str(log.punch_time))
				log.user_id = log.emp_code
				log.punch = log.punch_state
				log.status = 'IN' if str(log.punch_state) == "0" else 'OUT'

				if self.last_log_row and (log.timestamp < self.last_log_row):
					continue

				last_timestamp = last_log_users.get(log.user_id) or None
				if period and last_timestamp:
					diff = (log.timestamp - last_timestamp).seconds / 3600
					if diff < period:
						continue

				try:
					name = "{}-{}-{}".format(log.user_id,
												log.timestamp, log.status)
					frappe.db.sql("""
					INSERT IGNORE INTO `tabDevice Log`
					(name, employee, enroll_no, time, date, type, punch,
					 creation, modified, owner, device)
					VALUES
					(%s,
					 (SELECT name FROM tabEmployee WHERE attendance_device_id = %s LIMIT 1),
					 %s, %s, %s, %s, %s,
					 CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), %s, %s)
					""", (name, log.user_id, log.user_id, log.timestamp,
						  log.timestamp.date(), log.status, log.punch,
						  frappe.session.user, self.name))
					last_log_users[log.user_id] = log.timestamp
				except Exception:
					pass
				last = log.timestamp
			if last:
				self.last_log_row = min(last, datetime.now())

			frappe.db.commit()

		except Exception as e:
			frappe.msgprint(
				_("Process terminate : {}".format(e)), indicator='red')
			self.last_connection_error = str(e)
		finally:
			self.last_connection_time = datetime.now()
		
  
		self.get_after_mins = self.get_after_mins or 5
		self.excecution_time = datetime.now() + timedelta(minutes=self.get_after_mins)

		self.save()
		sync_employee()

@frappe.whitelist()
def sync_employee():
    frappe.db.sql("""
	Update `tabDevice Log` log set log.employee = (
	select name from tabEmployee where attendance_device_id = log.enroll_no limit 1
	)
	""")
    frappe.db.commit()
    frappe.msgprint(_("Done"))


@frappe.whitelist()
def get_active_device_logs(names=None):
	if names:
		names = json.loads(str(names))
	cur_time = datetime.now()
	sql = f""" 
		select name from `tabZK Device` where docstatus < 2 and auto_attendance = 1 and active = 1
	and ( STR_TO_DATE('{cur_time}', '%Y-%m-%d %T') >= excecution_time or ifnull(excecution_time,0)=0) ;
	"""
	print(sql)
	devices = names or frappe.db.sql_list(sql)
	# frappe.msgprint(f"""
	# 	select name from `tabZK Device` where docstatus < 2 and auto_attendance = 1
	# and ( STR_TO_DATE('{cur_time}', '%d-%m-%Y %T') >= excecution_time or ifnull(excecution_time,0)=0) ;
	# """)
	for device in devices:
		doc = frappe.get_doc("ZK Device", device)
		try:
			doc.get_device_log(fetch_next=True)
		except Exception as e:
			frappe.msgprint(
				_("Process terminate : {}".format(e)), indicator='red')


device_bio_map = {
	"id" : "device_id",
	"sn" : "serial_no",
	"ip_address" : "ip",
	"alias" : "alias",
	"area_name" : "area",
}


@frappe.whitelist()
def get_biotime_device_list():
	devices = get_devices_data() or []
	count = 0
	for device_data in devices:
		device_data = frappe._dict(device_data)
		if not device_data.get("sn"):
			continue

		exist = frappe.db.exists("ZK Device", {
			"serial_no": device_data.get("sn")
		})

		try:
			if exist:
				device = frappe.get_doc("ZK Device", exist)
			else:
				device = frappe.new_doc("ZK Device")

			for k, v in device_bio_map.items():
				setattr(device, v, device_data.get(k))

			if not exist:
				device.device_name = "{} - {}".format(
					device.alias or "Device",
					device.serial_no)
				device.get_data_type = "BioTime"
			device.save()
			count += 1
		except Exception as e:
			frappe.log_error(
				_("Failed to save BioTime device {0}: {1}").format(
					device_data.get("sn"), str(e)),
				"BioTime Device Sync")

	frappe.db.commit()
	frappe.msgprint(
		_("{0} device(s) fetched and synced from BioTime.").format(count),
		indicator="green")
