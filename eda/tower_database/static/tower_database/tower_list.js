/* Setup datatables for the tower listiongs */

"use strict";

// Get what to group by - only 'district' and 'bells' supported
const data = document.currentScript.dataset;
const group_by = data.group_by;
const table_id = data.table_id;

var column = null;
var direction = null;
if (group_by == 'district') {
	column = 4;
	direction = 'asc';
}
else if (group_by == 'bells') {
	column = 2;
	direction = 'desc';
}

// Build a datables config structure
var dt_options = {
	// No paging - we only have 200'ish towers
	paging: false,
	// Enable searchPanes for filtering
    layout: {
        topStart: {
            buttons: ['searchPanes'],
        }
    },
    columnDefs: [
    	// Disable the seachPane for Dedication
    	{
            target: 1,
            searchPanes: {
                show: false
            },
        }
    ]
};

if (column) {
    // Set the column to group by
    dt_options['rowGroup'] = { dataSrc: column };
	// Fix sorting on the group_by column
    dt_options['orderFixed'] = [ column, direction ];
    // Hide the group_by column
    dt_options['columnDefs'].push({
        target: column,
        visible: false,
        searchable: false
    })
};

$(document).ready( function () {
        $(`#${table_id}`).DataTable(dt_options);
});
