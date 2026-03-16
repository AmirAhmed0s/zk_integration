frappe.listview_settings["ZK Device"] = {
  onload: function (listview) {
    const method =
      "zk_integration.zk.doctype.zk_device.zk_device.get_active_device_logs";

    listview.page.add_action_item(__("Get Logs"), function () {
      listview.call_for_selected_items(method);
    });

    listview.page.add_inner_button(__("Get BioTime Devices"), function () {
      frappe.call({
        method:
          "zk_integration.zk.doctype.zk_device.zk_device.get_biotime_device_list",
        freeze: true,
        freeze_message: __("Fetching devices from BioTime..."),
        callback: function (r) {
          listview.refresh();
        },
      });
    });
  },
};
