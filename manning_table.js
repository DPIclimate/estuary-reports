/*
 * Create a table of latest readings.
 */
async function createValuesTable() {

	var dataset = {
		buoys: [],
		temperature: {
			values: [],
			trends: [],
			colors: []
		},
		salinity: {
			values: [],
			trends: [],
			colors: []
		},
		timestamp: {
			values: [],
			colors: []
		}
	};

	const temperature_data = {
		ids: [
			"64360b1772dc8c000da36c51",
			"64360b29c92fc7000cdfc961",
			"64360b0572dc8c000da36c44",
			"64360b5372dc8c000da36c6b"
		]
	};

	var ts_body = { 
		variables: temperature_data.ids,
		columns: ["device.name", "value.value", "timestamp"],
		join_dataframes: false,
		start: Math.floor(Date.now() - 3600000)
	};

	var options = {
		method: "POST",
		headers: {"x-auth-token": "BBAU-VOMMw42nHGcLPKVfBMQxYXDUiL78ln",
			"Content-Type": "application/json"
		},
		body: JSON.stringify(ts_body),
	};
	
	var response = await fetch("https://industrial.api.ubidots.com.au/api/v1.6/data/raw/series", 
			options).then(res => res.json());

	response.results.map(function(r, i) {
		if(r.length != 0) {

			var n = r.length;
			var sum = 0;
			var device_name = "Error";
			var init_ts = false;
			var ts = Math.floor(Date.now() - 3600000);

			var temp_values = [];
			r.map(function(v, i) {
				var trend = null;
				device_name = v[0];
				sum += v[1];
				temp_values.push(v[1]);
				if (init_ts == false) {
					ts = v[2];
					dataset.timestamp.colors.push("green");
					init_ts = true;
				}
			});

			var trend = " &#8212;";
			var diff = 0;
			if (temp_values.length > 1) {
				diff = temp_values[0] - temp_values[temp_values.length - 1];
			}
			if (diff > 0) {
				trend = " &darr;";
			} else if (diff < 0){
				trend = " &uarr;";
			}

			dataset.temperature.trends.push(trend);

			var average = (sum / n);
			if(average >= 28) {
				dataset.temperature.colors.push("red");
			} else if (average > 24 && average < 28) {
				dataset.temperature.colors.push("orange");
			} else {
				dataset.temperature.colors.push("#0645ad");
			}

			const ts_options = {
				hour: "numeric",
				minute: "numeric",
				day: "numeric",
				month: "short"
			};

			if(init_ts == false) {
				dataset.timestamp.colors.push("red");
			}

			ts = new Date(ts);
			ts = ts.toLocaleDateString("en-US", ts_options);
			dataset.temperature.values.push(average.toFixed(1));
			dataset.timestamp.values.push(ts);
			dataset.buoys.push(device_name);
		}
	})


	const salinity_data = {
		ids: [
			"64360b1472dc8c000da36c50",
			"64360b2772dc8c000da36c58",
			"64360b0416a090000c41ef46",
			"64360b5272dc8c000da36c6a"
		]
	}

	ts_body = { 
		variables: salinity_data.ids,
		columns: ["device.name", "value.value", "timestamp"],
		join_dataframes: false,
		start: Math.floor(Date.now() - 3600000)
	};


	options = {
		method: "POST",
		headers: {"x-auth-token": "BBAU-VOMMw42nHGcLPKVfBMQxYXDUiL78ln",
			"Content-Type": "application/json"
		},
		body: JSON.stringify(ts_body),
	};

	response = await fetch("https://industrial.api.ubidots.com.au/api/v1.6/data/raw/series", 
			options).then(res => res.json());

	response.results.map(function(r, i) {
		if(r.length != 0) {
			var n = r.length;
			var sum = 0;
			var temp_values = [];
			r.map(function(v, i) {
				sum += v[1];
				temp_values.push(v[1]);
			});

			var trend = " &#8212;";
			var diff = 0;
			if (temp_values.length > 1) {
				diff = temp_values[0] - temp_values[temp_values.length - 1];
			}
			if (diff > 0) {
				trend = " &darr;";
			} else if (diff < 0){
				trend = " &uarr;";
			}

			dataset.salinity.trends.push(trend);

			var average = (sum / n);
			if(average >= 22 && average < 50) {
				dataset.salinity.colors.push("green");
			} else if (average > 16 && average < 22) {
				dataset.salinity.colors.push("orange")
			} else {
				dataset.salinity.colors.push("red");
			}

			dataset.salinity.values.push(average.toFixed(1));
		}
	})
	
	var table_head = document.getElementById("data-head");
	var head = table_head.insertRow(0);
	head.insertCell(0).innerHTML = "Buoy";
	head.insertCell(1).innerHTML = "Salinity";
	head.insertCell(2).innerHTML = "Temperature";
	head.insertCell(3).innerHTML = "Date";

	dataset.buoys.map(function(b, i) {
		const table = document.getElementById("data-body");
		var row = table.insertRow(0);
		var buoy = row.insertCell(0);
		var salinity = row.insertCell(1);
		var temperature = row.insertCell(2);
		var date = row.insertCell(3);
		buoy.innerHTML = b;
		salinity.innerHTML = dataset.salinity.values[i] + dataset.salinity.trends[i];
		salinity.style.color = dataset.salinity.colors[i];
		temperature.innerHTML = dataset.temperature.values[i] + dataset.temperature.trends[i];
		temperature.style.color = dataset.temperature.colors[i];
		date.innerHTML = dataset.timestamp.values[i];
		date.style.color = dataset.timestamp.colors[i];
	});

	let table = new DataTable("#data-table", {
		"order": [[0, 'asc']],
		"lengthChange": false,
		"info": false,
		"searching": false,
		"paging": false
	});
}
