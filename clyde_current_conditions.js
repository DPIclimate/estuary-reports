/*
 * Gathers weather station data from an AWS linked to Ubidots.
 * Used chart.js as the backend for creating a chart.
 * Sets the inner HTML of some variables to display the most
 * recent values.
 */
async function getTempAndHumid() {
	const UBIDOTS_BASE_URL = "https://industrial.api.ubidots.com.au/api/v1.6";
	const UBIDOTS_TOKEN = "BBAU-5C7fdQtm2qlveEOSDc0gCk85e7a5Sa";

	async function fetchRawSeries(variableIds, startMs) {
		const body = {
			variables: variableIds,
			columns: ["value.value", "timestamp"],
			join_dataframes: false,
			start: Math.floor(startMs)
		};

		const options = {
			method: "POST",
			headers: {
				"x-auth-token": UBIDOTS_TOKEN,
				"Content-Type": "application/json"
			},
			body: JSON.stringify(body)
		};

		const res = await fetch(`${UBIDOTS_BASE_URL}/data/raw/series`, options);
		if (!res.ok) {
			throw new Error(`Ubidots raw series request failed (${res.status})`);
		}
		const json = await res.json();
		return Array.isArray(json?.results) ? json.results : [];
	}

	function sortByTimestampAscending(points) {
		return points.slice(0).sort((a, b) => a.x - b.x);
	}

	function alignSeriesToTimestamps(primaryTimestamps, seriesPoints) {
		const lookup = new Map();
		seriesPoints.forEach(p => lookup.set(p.x, p.y));
		return primaryTimestamps.map(ts => ({ x: ts, y: lookup.has(ts) ? lookup.get(ts) : null }));
	}

	function degreesToCompassLabel(degrees) {
		const wind_dir = [
			{ direction: 0, value: "N" },
			{ direction: 22.5, value: "NNE" },
			{ direction: 45, value: "NE" },
			{ direction: 67.5, value: "ENE" },
			{ direction: 90, value: "E" },
			{ direction: 112.5, value: "ESE" },
			{ direction: 135, value: "SE" },
			{ direction: 157.5, value: "SSE" },
			{ direction: 180, value: "S" },
			{ direction: 202.5, value: "SSW" },
			{ direction: 225, value: "SW" },
			{ direction: 247.5, value: "WSW" },
			{ direction: 270, value: "W" },
			{ direction: 292.5, value: "WNW" },
			{ direction: 315, value: "NW" },
			{ direction: 337.5, value: "NNW" },
		];

		const v = Number(degrees);
		if (!Number.isFinite(v)) {
			return null;
		}

		let minDiff = Infinity;
		let label = "N";
		wind_dir.forEach(d => {
			const diff = Math.abs(d.direction - v);
			if (diff < minDiff) {
				minDiff = diff;
				label = d.value;
			}
		});
		return label;
	}

	var dataset = {
		temperature: {
			values: [],
			colors: []
		},
		humidity: {
			values: [],
			colors: []
		},
		wind: {
			speed: [],
			direction: [],
			colors: []
		},
	};
	
	// Variables
	const air_temperature_var = "61788e45852f090346add2bd";
	const humidity_var = "61788e47dc917002aa2562e0";
	const wind_speed_var = "61788e49dc917002e7774656";
	const wind_dir_var = "61788e48852f0902cbf8756f";

	const startMs = Date.now() - 604800000; // 7 days
	const [tempRows, humidRows, windSpeedRows, windDirRows] = await fetchRawSeries(
		[air_temperature_var, humidity_var, wind_speed_var, wind_dir_var],
		startMs
	);

	function rowsToPoints(rows, valueToY) {
		if (!Array.isArray(rows)) {
			return [];
		}
		// rows are [value.value, timestamp]
		const points = rows.map(v => {
			const value = Array.isArray(v) ? v[0] : null;
			const ts = Array.isArray(v) ? v[1] : null;
			const x = Number(ts);
			if (!Number.isFinite(x)) {
				return null;
			}
			return { x, y: valueToY(value) };
		}).filter(Boolean);
		return sortByTimestampAscending(points);
	}

	dataset.temperature.values = rowsToPoints(tempRows, (value) => {
		const v = Number(value);
		if (Number.isFinite(v) && v < 50 && v >= -10) {
			return parseFloat(v.toFixed(1));
		}
		return null;
	});

	dataset.humidity.values = rowsToPoints(humidRows, (value) => {
		const v = Number(value);
		if (Number.isFinite(v) && v < 100.1 && v >= 0) {
			return parseFloat(v.toFixed(1));
		}
		return null;
	});

	dataset.wind.speed = rowsToPoints(windSpeedRows, (value) => {
		const v = Number(value);
		const windKnts = v * 1.9438445;
		if (Number.isFinite(windKnts) && windKnts < 60 && windKnts >= 0) {
			return parseFloat(windKnts.toFixed(1));
		}
		return null;
	});

	dataset.wind.direction = rowsToPoints(windDirRows, (value) => degreesToCompassLabel(value));

	// Align humidity/wind arrays to temperature timestamps so tooltip indexing stays consistent.
	const primaryTimestamps = dataset.temperature.values.map(p => p.x);
	if (primaryTimestamps.length > 0) {
		dataset.humidity.values = alignSeriesToTimestamps(primaryTimestamps, dataset.humidity.values);
		dataset.wind.speed = alignSeriesToTimestamps(primaryTimestamps, dataset.wind.speed);
		dataset.wind.direction = alignSeriesToTimestamps(primaryTimestamps, dataset.wind.direction);
	}

	const ts_options = {
		day: "numeric",
		month: "short"
	};

	const data = {
		datasets: [
			{
				label: 'Air Temperature',
				backgroundColor: 'rgb(255, 99, 132)',
				borderColor: 'rgb(255, 99, 132)',
				showLine: true,
				pointRadius: 0,
				tension: 0.4,
				data: dataset.temperature.values,
				yAxisID: 'y'
			},
			{
				label: 'Humidity',
				backgroundColor: "#1BA098",
				borderColor: "#1BA098",
				showLine: true,
				pointRadius: 0,
				tension: 0.4,
				data: dataset.humidity.values,
				yAxisID: 'y1'
			},
			{
				label: 'Wind Speed',
				backgroundColor: "#1D1D2C",
				borderColor: "#1D1D2C",
				showLine: true,
				pointRadius: 0,
				tension: 0.4,
				data: dataset.wind.speed,
				yAxisID: 'y'
			},
			{
				label: 'Wind Direction',
				hidden: true,
				backgroundColor: "#1D1D2C",
				borderColor: "#1D1D2C",
				showLine: true,
				pointRadius: 0,
				tension: 0.4,
				data: dataset.wind.direction,
				yAxisID: 'y'
			}
		]
	};

	// Check if its night time
	function isNight(ts) {
		return ts.getHours() < 7 || ts.getHours() > 18;
	}

	// Identifiy and extract points that represent night time 
	// Used to create night boxes (grey shadows) below
	var night_intervals = [];
	var night = false;
	if (dataset.temperature.values.length > 0) dataset.temperature.values.map(function(v, i) {
		var ts = new Date(v.x);
		if(isNight(ts)) {
			if (night == false) {
				night_intervals.push(i);
				night = true;
			}
		} else {
			if (night == true) {
				night_intervals.push(i-1);
			}
			night = false;
		}
	});

	// Generate boxes that represent night time.
	const night_boxes = [];
	for (var i = 0; i < night_intervals.length - 1; i+=2){
		// Accounts for data currently being night time
		var box = {
			type: 'box',
			xMin: dataset.temperature.values[night_intervals[i]].x,
			xMax: dataset.temperature.values[night_intervals[i+1]].x,
			drawTime: "beforeDraw",
			yMin: 0,
			yMax: 50,
			backgroundColor: 'rgba(221, 221, 221, 0.4)',
			borderWidth: 0
		}
		night_boxes.push(box);
	}

	// Extra box needed if its currently night time
	if(night_intervals.length % 2 != 0) {
		var box = {
			type: 'box',
			xMin: dataset.temperature.values[night_intervals[night_intervals.length - 1]].x,
			xMax: dataset.temperature.values[dataset.temperature.values.length - 1].x,
			drawTime: "beforeDraw",
			yMin: 0,
			yMax: 50,
			backgroundColor: 'rgba(221, 221, 221, 0.4)',
			borderWidth: 0
		}
		night_boxes.push(box);
	}

	const xMin = dataset.temperature.values[0]?.x;
	const xMax = dataset.temperature.values[dataset.temperature.values.length - 1]?.x;

	const config = {
		type: 'scatter',
		data: data,
		options: {
			maintainAspectRatio: false,
			responseive: true,
			interaction: {
				intersect: false,
				axis: "x",
				mode: "index"
			},
			showLine: true,
			scales: {
				x: {
					min: xMin,
					max: xMax,
					ticks: {
						callback: function(v, i) {
							var ts = new Date(v);
							ts = ts.toLocaleDateString("en-US", ts_options);
							return ts;
						},
						major: {
							enabled: true,
						},
						maxRotation: 0,
						minRotation: 0,
						maxTicksLimit: 7,
						minTicksLimit: 7,
						font: {
							size: 14
						}
					},
				},
				y: {
					title: {
						display: false,
						text: "Temperature (C)",
						color: "rgb(255, 99, 132)",
						font: {
							size: 14
						}
					},
					position: "right",
					ticks: {
						color: "rgb(255, 99, 132)",
						font: {
							size: 14
						}
					}, 
					min: 0, 
					max: 50
				},
				y1: {
					title: {
						display: false,
						text: "Humidity (%)",
						color: "#1BA098",
						font: {
							size: 14
						}
					},
					position: "left",
					ticks: {
						color: "#1BA098",
						font: {
							size: 14
						}
					},
					min: 0,
					max: 100
				}
			},
			plugins: {
				legend: {
					labels: {
						filter: function(v, _) {
							return !v.text.includes("Wind Direction");
						},
						font: {
							size: 14
						}
					}
				},
				tooltip: {
					enabled: false
				},
				zoom: {
					pan: {
						enabled: true,
						mode: "x",
					},
					zoom: {
						pinch: {
							enabled: true
						},
						wheel: {
							enabled: false 
						},
						mode: "x"
					},
					limits: {
						x: {
							min: xMin != null ? new Date(xMin).valueOf() : undefined,
							max: xMax != null ? new Date(xMax).valueOf() : undefined
						}
					},
				},
				annotation: {
					annotations: night_boxes
				},
			}
		},
		plugins: [{
			afterDraw: function(chart) {
				if (chart.tooltip?._active?.length) {
					let x = chart.tooltip._active[0].element.x;
					let idx = chart.tooltip._active[0].index;

					const date_opts = {
						hour: "numeric",
						day: "numeric",
						month: "short"
					}
					
					if(idx > dataset.temperature.values.length - 1) {
						idx = dataset.temperature.values.length - 1;
					}
					if (idx < 0 || dataset.temperature.values.length === 0) {
						return;
					}
					var ts = new Date(dataset.temperature.values[idx].x);
					ts = ts.toLocaleDateString("en-US", date_opts);
					document.getElementById("date-value").innerHTML = ts;

					// Temperature
					if(dataset.temperature.values[idx].y != null){
						document.getElementById("temperature-value").innerHTML = dataset.temperature
							.values[idx].y + " &deg;C";
					} else {
						document.getElementById("temperature-value").innerHTML = "No Data.";
					}

					// Humidity
					if(idx > dataset.humidity.values.length - 1) {
						idx = dataset.humidity.values.length - 1;
					}
					if(dataset.humidity.values[idx].y != null) {
						document.getElementById("humidity-value").innerHTML = dataset.humidity
							.values[idx].y + " %";
					} else {
						document.getElementById("humidity-value").innerHTML = "No Data.";
					}

					// Wind speed
					if(idx > dataset.wind.speed.length - 1) {
						idx = dataset.wind.speed.length - 1;
					}
					const windDir = dataset.wind.direction?.[idx]?.y;
					if(dataset.wind.speed?.[idx]?.y != null){
						document.getElementById("wind-value").innerHTML = dataset.wind.speed[idx].y + 
							" kn " + (windDir ?? "");
					} else {
						document.getElementById("wind-value").innerHTML = "No Data.";
					}

					chart.ctx.save();
					chart.ctx.beginPath();
					chart.ctx.moveTo(x, chart.scales.y.top);
					chart.ctx.lineTo(x, chart.scales.y.bottom);
					chart.ctx.lineWidth = 2;
					chart.ctx.strokeStyle = '#000000';
					chart.ctx.stroke();
					chart.ctx.restore();
				}
				else {
					var idx = dataset.temperature.values.length - 1;
					if (idx < 0) {
						document.getElementById("date-value").innerHTML = "No Data.";
						document.getElementById("temperature-value").innerHTML = "No Data.";
						document.getElementById("humidity-value").innerHTML = "No Data.";
						document.getElementById("wind-value").innerHTML = "No Data.";
						return;
					}
					var ts = new Date(dataset.temperature.values[idx].x);
					ts = ts.toLocaleDateString("en-US", date_opts);
					document.getElementById("date-value").innerHTML = ts 
					document.getElementById("temperature-value").innerHTML = dataset.temperature
						.values[idx].y + " &deg;C";
					idx = dataset.humidity.values.length - 1;
					document.getElementById("humidity-value").innerHTML = dataset.humidity
						.values[idx].y + " %";
					idx = dataset.wind.speed.length - 1;
					const windDir = dataset.wind.direction?.[idx]?.y;
					document.getElementById("wind-value").innerHTML = dataset.wind.speed[idx].y + 
						" kn " + (windDir ?? "");
				}
			},

		}]
	};

	const date_opts = {
		hour: "numeric",
		day: "numeric",
		month: "short"
	}

	if (dataset.temperature.values.length > 0) {
		var idx = dataset.temperature.values.length - 1;
		var ts = new Date(dataset.temperature.values[idx].x);
		ts = ts.toLocaleDateString("en-US", date_opts);
		document.getElementById("date-value").innerHTML = ts 
		document.getElementById("temperature-value").innerHTML = dataset.temperature
			.values[idx].y + " &deg;C";
		idx = dataset.humidity.values.length - 1;
		document.getElementById("humidity-value").innerHTML = dataset.humidity
			.values[idx].y + " %";
		idx = dataset.wind.speed.length - 1;
		const windDir = dataset.wind.direction?.[idx]?.y;
		document.getElementById("wind-value").innerHTML = dataset.wind.speed[idx].y + 
			" kn " + (windDir ?? "");
	} else {
		document.getElementById("date-value").innerHTML = "No Data.";
		document.getElementById("temperature-value").innerHTML = "No Data.";
		document.getElementById("humidity-value").innerHTML = "No Data.";
		document.getElementById("wind-value").innerHTML = "No Data.";
	}
	document.getElementById("table-info").innerHTML = "&darr; decreasing, &#8212; stable, &uarr; increasing (based on data from the past hour)";

	return config;
}

