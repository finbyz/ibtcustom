cur_frm.fields_dict.leave_type.get_query = function(doc) {
	return {
		filters: {
			"status": 'Enable'
		}
	}
};