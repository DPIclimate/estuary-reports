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
		},
		temperature_ids: [],
		salinity_ids: []
	};

	const temperature_data = {
		ids: [
			"620c34a236478d1df15fcd03",
			"6181b4e2852f0907a66ca28b",
			"61788ec5dc917002aa2562e2",
			"61788eb9a73c3401fa330fbf",
			"6174a4cddc9170000d0c6be1",
			"61732bf7852f09000e22a105",
			"617318d1852f09000e22a102",
			"6171f4d686f43b04efae2d48",
			"616e4a88810cbd039c60af03",
			"616e493d810cbd03d916fa69",
			"616e476e41ac9d03d99b67ed"
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
		headers: {"x-auth-token": "BBAU-vf8qa7Ca1UN8eQlyB9Md2JTfK77Ezr",
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
			"620c34a036478d1df15fcd01",
			"6181b4e0a73c34080beda0d7",
			"61788ec4a73c3402b041fb61",
			"61788eb8a73c34027320e15e",
			"6174a4cc852f09011427403b",
			"61732bf6852f09000d3d1bff",
			"617318d0dc9170000d0c6bbc",
			"6171f4d5810cbd25005c19e4",
			"616e4a8741ac9d039cfa39f8",
			"616e493c810cbd03d916fa68",
			"616e476d41ac9d03d99b67ec"
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

			dataset.salinity_ids.push(salinity_data.ids[i]);
			dataset.temperature_ids.push(temperature_data.ids[i]);
		}
	})
	
	var table_head = document.getElementById("data-head");
	var head = table_head.insertRow(0);
	head.insertCell(0).innerHTML = "Buoy";
	head.insertCell(1).innerHTML = "Salinity";
	head.insertCell(2).innerHTML = "Temperature";
	head.insertCell(3).innerHTML = "Date";
	head.insertCell(4).innerHTML = "Historical";

	// console.log(dataset)

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

		// Create a new cell for the chart button
		var chartCell = row.insertCell(4);

		// Create a chart button for each row
		var chartButton = document.createElement("button");
		chartButton.innerHTML = "&#x1F4C8;"; // Chart Icon.
		chartButton.addEventListener("click", function () {
			console.log("Dataset");
			console.log(dataset);
			openChartPopup(b, dataset.salinity_ids[i], dataset.temperature_ids[i]);
		});
		chartCell.appendChild(chartButton);
	});

	let table = new DataTable("#data-table", {
		"order": [[0, 'asc']],
		"lengthChange": false,
		"info": false,
		"searching": false,
		"paging": false
	});
}


function openChartPopup(buoy, sal_id, temp_id) {
	// Create a popup window for the chart
	var popup = window.open("", "Chart Popup", "width=600,height=400");
	popup.document.title = buoy; // Set the title of the popup window to the name of the buoy

	// After creating popup window, display spinning loading symbol whilst data is being retrieved.
	popup.document.body.innerHTML = '<div class="loading-spinner"></div>';

	// CSS styles for the loading spinner
	const spinnerStyles = `
		.loading-spinner {
			width: 40px;
			height: 40px;
			border-radius: 50%;
			border: 4px solid #f3f3f3;
			border-top: 4px solid #3498db;
			animation: spin 1s linear infinite;
			position: absolute;
			top: 50%;
			left: 50%;
			transform: translate(-50%, -50%);
		}

		@keyframes spin {
			0% { transform: rotate(0deg); }
			100% { transform: rotate(360deg); }
		}
	`;

	// Create a <style> element and append the CSS styles to it
	const styleElement = popup.document.createElement('style');
	styleElement.innerHTML = spinnerStyles;
	popup.document.head.appendChild(styleElement);

	// Get the current year
	const currentYear = new Date().getFullYear();

	// Calculate the start and end timestamps for the current year
	const endTimestamp = new Date().getTime();
	const startTimestamp = endTimestamp - (365 * 24 * 60 * 60 * 1000);

	// Example: Fetch data for the provided device IDs.
	fetch("https://industrial.api.ubidots.com/api/v1.6/data/raw/series", {
		method: "POST",
		headers: {
			"X-Auth-Token": "BBAU-VOMMw42nHGcLPKVfBMQxYXDUiL78ln",
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			variables: [sal_id, temp_id],
			columns: ["value.value", "timestamp"],
			join_dataframes: false,
			start: startTimestamp,
			end: endTimestamp,
		}),
	})
	.then((res) => res.json())
	.then((response) => {
		// Extract the salinity and temperature data from the response
		const timestampData = response.results[0].map((entry) => {
			const timestamp = new Date(entry[1]);
			return timestamp.toLocaleString(); // Convert timestamp to human-readable format
		}).reverse();

		const salinityData = response.results[0].map((entry) => entry[0]).reverse();

		const temperatureData = response.results[1].map((entry) => entry[0]).reverse();

		// Combine the salinity and temperature data into an array for plotting
		const chartData = salinityData.map((salinity, index) => ({
			salinity,
			temperature: temperatureData[index],
			timestamp: timestampData[index],
		}));

		// Create a new canvas element
		const canvas = popup.document.createElement("canvas");
		canvas.id = "chartCanvas";

		// Remove the loading message
		popup.document.body.innerHTML = "";

		popup.document.body.appendChild(canvas);

		var ctx = canvas.getContext("2d");
		new Chart(ctx, {
			type: "line",
			data: {
				labels: chartData.map((data) => data.timestamp),
				datasets: [
					{
						label: "Salinity",
						data: chartData.map((data) => data.salinity),
						borderColor: "blue",
						fill: false,
					},
					{
						label: "Temperature",
						data: chartData.map((data) => data.temperature),
						borderColor: "red",
						fill: false,
					},
				],
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
			},
		});

	})
	.catch((error) => {
		// Handle any errors
		console.error(error);
	});

}

