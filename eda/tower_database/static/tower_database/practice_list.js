/* Setup datatables for the tower listiongs */

"use strict";

// Get what to group by - only 'district' and 'bells' supported
const data = document.currentScript.dataset;
const table_id = data.table_id;

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
    rowGroup: {
        dataSrc: 1
    },
    orderFixed: [
        0, 'asc'
    ],
    columnDefs: [
        {
            targets: [0, 1],
            visible: false,
            searchable: false,
            searchPanes: {
                show: false
            },
        },
        {
            target: 5,
            orderable: false,
            searchable: false,
        },
    ]
};

$(document).ready( function () {
        $(`#${table_id}`).DataTable(dt_options);
});
