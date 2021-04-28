frappe.ui.form.on("Expense Claim", {
    onload: function(frm) {
        if(!frm.doc.__islocal){
            cur_frm.set_df_property("title", "read_only",1);
        }
        else{
            cur_frm.set_df_property("title", "read_only",0);
        }
    }
});