frappe.listview_settings['Leave Type'] = {
    add_fields: ["status"],
    get_indicator: function (doc) {
        return [__(doc.status), {
            "Enable": "blue",
            "Disable": "grey",
        } [doc.status], "status,=," + doc.status];
    }
};