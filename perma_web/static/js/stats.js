var margin = {top: 20, right: 20, bottom: 30, left: 50},
                            width = 960 - margin.left - margin.right,
                            height = 500 - margin.top - margin.bottom;

var parseDate = d3.time.format("%y-%b-%d").parse,
    formatPercent = d3.format(".0%");

var x = d3.time.scale()
    .range([0, width]);

var y = d3.scale.linear()
    .range([height, 0]);

var draw_folks_vis = function(){

	var format = d3.time.format.iso; //d3.time.format("%d-%b-%y");

	var x = d3.time.scale()
	    .range([0, width]);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var z = d3.scale.category20();

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom")
	    .ticks(d3.time.weeks);

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left");

	var stack = d3.layout.stack()
	    .offset("zero")
	    .values(function(d) { return d.values; })
	    .x(function(d) { return d.date; })
	    .y(function(d) { return d.value; });

	var nest = d3.nest()
	    .key(function(d) { return d.key; });

	var area = d3.svg.area()
	    .interpolate("cardinal")
	    .x(function(d) { return x(d.date); })
	    .y0(function(d) { return y(d.y0); })
	    .y1(function(d) { return y(d.y0 + d.y); });

	var svg = d3.select("#folks-vis").append("svg")
        .attr("width", "100%")
        .attr('viewBox', '0 0 ' + String(width + margin.left + margin.right) + ' ' + String(height + margin.top + margin.bottom))
        .attr('perserveAspectRatio', 'none')
        .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.csv(stats_users_url, function(data) {
	  data.forEach(function(d) {
	    d.date = format.parse(d.date);
		d.name= 'some name here';
	    d.value = +d.value;
	  });

	  var layers = stack(nest.entries(data));

	  x.domain(d3.extent(data, function(d) { return d.date; }));
	  y.domain([0, d3.max(data, function(d) { return d.y0 + d.y; })]);

	  svg.selectAll(".layer")
	      .data(layers)
	    .enter().append("path")
	      .attr("class", "layer")
	      .attr("d", function(d) { return area(d.values); })
	      .style("fill", function(d, i) { return z(i); });
	
	var total_users = 0;
	
	svg.selectAll("text")
        .data(layers)
        .enter()
        .append("text")
      .datum(function(d) { return {name: d.key, value: d.values[d.values.length - 1]}; })
		.attr("y", function(d) {return y(d.value.y0 + d.value.y / 2); })
		.attr("x", 885)
		.attr("font-size", "14px")
		.attr("style", "text-anchor: end")
		.text( function (d) { total_users = total_users+ d.value.y; return d.name + ", " + d.value.y; });

	  // Set the total link count in our text description of hte vis
	  d3.select('#user_count').text(total_users);
	
	  svg.append("g")
	      .attr("class", "x axis")
	      .attr("transform", "translate(0," + height + ")")
	      .call(xAxis);

	  svg.append("g")
	      .attr("class", "y axis")
	      .call(yAxis)
	    .append("text")
	      .attr("transform", "rotate(-90)")
	      .attr("y", 6)
	      .attr("dy", ".71em")
	      .style("text-anchor", "end")
	      .text("Users");
	
	});
}

var draw_vesting_orgs_vis = function(){
	
	var format = d3.time.format.iso;
	
	var x = d3.time.scale()
	    .range([0, width]);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom")
	    .ticks(d3.time.weeks);

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left");

	var line = d3.svg.line()
	    .x(function(d) { return x(d.date); })
	    .y(function(d) { return y(d.close); });

	var svg = d3.select("#vestings-org-vis").append("svg")
	    .attr("width", "100%")
        .attr('viewBox', '0 0 ' + String(width + margin.left + margin.right) + ' ' + String(height + margin.top + margin.bottom))
        .attr('perserveAspectRatio', 'none')
        .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.csv(stats_vesting_orgs_url, function(error, data) {
	  data.forEach(function(d) {
	    d.date = format.parse(d.date);
	    d.close = +d.close;
	  });

	  // Super kludgy way to get latest size. TODO: improve.
	  var latest_size = 0;

	  x.domain(d3.extent(data, function(d) { return d.date; }));
	  y.domain(d3.extent(data, function(d) { latest_size = d.close; return d.close; }));

	  // Set the total size of store in our text description of the vis
	  d3.select('#vesting_org_count').text(latest_size);

	  svg.append("g")
	      .attr("class", "x axis")
	      .attr("transform", "translate(0," + height + ")")
	      .call(xAxis);

	  svg.append("g")
	      .attr("class", "y axis")
	      .call(yAxis)
	    .append("text")
	      .attr("transform", "rotate(-90)")
	      .attr("y", 6)
	      .attr("dy", ".71em")
	      .style("text-anchor", "end")
	      .text("Vesting Orgs");

	  svg.append("path")
	      .datum(data)
	      .attr("class", "line")
	      .attr("d", line);
	});
}

var draw_registrar_vis = function(){
	
	var format = d3.time.format.iso;
	
	var x = d3.time.scale()
	    .range([0, width]);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom")
	    .ticks(d3.time.weeks);

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left");

	var line = d3.svg.line()
	    .x(function(d) { return x(d.date); })
	    .y(function(d) { return y(d.close); });

	var svg = d3.select("#registrars-vis").append("svg")
        .attr("width", "100%")
        .attr('viewBox', '0 0 ' + String(width + margin.left + margin.right) + ' ' + String(height + margin.top + margin.bottom))
        .attr('perserveAspectRatio', 'none')
        .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.csv(stats_registrars_url, function(error, data) {
	  data.forEach(function(d) {
	    d.date = format.parse(d.date);
	    d.close = +d.close;
	  });

	  // Super kludgy way to get latest size. TODO: improve.
	  var latest_size = 0;

	  x.domain(d3.extent(data, function(d) { return d.date; }));
	  y.domain(d3.extent(data, function(d) { latest_size = d.close; return d.close; }));

	  // Set the total size of store in our text description of the vis
	  d3.select('#library_count').text(latest_size);

	  svg.append("g")
	      .attr("class", "x axis")
	      .attr("transform", "translate(0," + height + ")")
	      .call(xAxis);

	  svg.append("g")
	      .attr("class", "y axis")
	      .call(yAxis)
	    .append("text")
	      .attr("transform", "rotate(-90)")
	      .attr("y", 6)
	      .attr("dy", ".71em")
	      .style("text-anchor", "end")
	      .text("Libraries");

	  svg.append("path")
	      .datum(data)
	      .attr("class", "line")
	      .attr("d", line);
	});
}


var draw_hits_vis = function(){
	
	var parseDate = d3.time.format("%d-%b-%y").parse;
	
	var x = d3.time.scale()
	    .range([0, width]);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom")
	    .ticks(d3.time.weeks);

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left");

	var line = d3.svg.line()
	    .x(function(d) { return x(d.date); })
	    .y(function(d) { return y(d.close); });

	var svg = d3.select("#hits-vis").append("svg")
        .attr("width", "100%")
        .attr('viewBox', '0 0 ' + String(width + margin.left + margin.right) + ' ' + String(height + margin.top + margin.bottom))
        .attr('perserveAspectRatio', 'none')
        .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.tsv(static_prefix + "stats/hits-data.tsv", function(error, data) {
	  data.forEach(function(d) {
	    d.date = parseDate(d.date);
	    d.close = +d.close;
	  });

	  x.domain(d3.extent(data, function(d) { return d.date; }));
	  y.domain(d3.extent(data, function(d) { return d.close; }));

	  svg.append("g")
	      .attr("class", "x axis")
	      .attr("transform", "translate(0," + height + ")")
	      .call(xAxis);

	  svg.append("g")
	      .attr("class", "y axis")
	      .call(yAxis)
	    .append("text")
	      .attr("transform", "rotate(-90)")
	      .attr("y", 6)
	      .attr("dy", ".71em")
	      .style("text-anchor", "end")
	      .text("Hits");

	  svg.append("path")
	      .datum(data)
	      .attr("class", "line")
	      .attr("d", line);
	});
}



var draw_links_vis = function(){

	var format = d3.time.format.iso; // d3.time.format("%d-%b-%y");

	var x = d3.time.scale()
	    .range([0, width]);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var z = d3.scale.category20();

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom")
	    .ticks(d3.time.weeks);

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left");

	var stack = d3.layout.stack()
	    .offset("zero")
	    .values(function(d) { return d.values; })
	    .x(function(d) { return d.date; })
	    .y(function(d) { return d.value; });

	var nest = d3.nest()
	    .key(function(d) { return d.key; });

	var area = d3.svg.area()
	    .interpolate("cardinal")
	    .x(function(d) { return x(d.date); })
	    .y0(function(d) { return y(d.y0); })
	    .y1(function(d) { return y(d.y0 + d.y); });

	var svg = d3.select("#links-vis").append("svg")
        .attr("width", "100%")
        .attr('viewBox', '0 0 ' + String(width + margin.left + margin.right) + ' ' + String(height + margin.top + margin.bottom))
        .attr('perserveAspectRatio', 'none')
        .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.csv(stats_links_url, function(data) {
	  data.forEach(function(d) {
	    d.date = format.parse(d.date);
		d.name= 'some name here';
	    d.value = +d.value;
	  });

	  var layers = stack(nest.entries(data));

	  x.domain(d3.extent(data, function(d) { return d.date; }));
	  y.domain([0, d3.max(data, function(d) { return d.y0 + d.y; })]);

	  svg.selectAll(".layer")
	      .data(layers)
	    .enter().append("path")
	      .attr("class", "layer")
	      .attr("d", function(d) { return area(d.values); })
	      .style("fill", function(d, i) { return z(i); });
	
	var total_links = 0;
	
	svg.selectAll("text")
        .data(layers)
        .enter()
        .append("text")
      .datum(function(d) { return {name: d.key, value: d.values[d.values.length - 1]}; })
		.attr("y", function(d) { return y(d.value.y0 + d.value.y / 2); })
		.attr("x", 885)
		.attr("font-size", "13px")
		.attr("style", "text-anchor: end")
		.text( function (d) { total_links = total_links + d.value.y;  return d.name + ", " + d.value.y; });

	  // Set the total link count in our text description of hte vis
	  d3.select('#link_count').text(total_links);
		
	  svg.append("g")
	      .attr("class", "x axis")
	      .attr("transform", "translate(0," + height + ")")
	      .call(xAxis);

	  svg.append("g")
	      .attr("class", "y axis")
	      .call(yAxis)
	    .append("text")
	      .attr("transform", "rotate(-90)")
	      .attr("y", 6)
	      .attr("dy", ".71em")
	      .style("text-anchor", "end")
	      .text("Links");
	
	});
}

var draw_darchive_vis = function(){

	var format = d3.time.format.iso; // d3.time.format("%d-%b-%y");
	
	var x = d3.time.scale()
	    .range([0, width]);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var z = d3.scale.category20();

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom")
	    .ticks(d3.time.weeks);

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left");

	var stack = d3.layout.stack()
	    .offset("zero")
	    .values(function(d) { return d.values; })
	    .x(function(d) { return d.date; })
	    .y(function(d) { return d.value; });

	var nest = d3.nest()
	    .key(function(d) { return d.key; });

	var area = d3.svg.area()
	    .interpolate("cardinal")
	    .x(function(d) { return x(d.date); })
	    .y0(function(d) { return y(d.y0); })
	    .y1(function(d) { return y(d.y0 + d.y); });

	var svg = d3.select("#darchive-vis").append("svg")
        .attr("width", "100%")
        .attr('viewBox', '0 0 ' + String(width + margin.left + margin.right) + ' ' + String(height + margin.top + margin.bottom))
        .attr('perserveAspectRatio', 'none')
        .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.csv(stats_darchived_links_url, function(data) {
	  data.forEach(function(d) {
	    d.date = format.parse(d.date);
		d.name= 'some name here';
	    d.value = +d.value;
	  });

	  var layers = stack(nest.entries(data));

	  x.domain(d3.extent(data, function(d) { return d.date; }));
	  y.domain([0, d3.max(data, function(d) { if (d.y0 + d.y <=10){ return 10;} else {return d.y0 + d.y; }})]);

	  svg.selectAll(".layer")
	      .data(layers)
	    .enter().append("path")
	      .attr("class", "layer")
	      .attr("d", function(d) { return area(d.values); })
	      .style("fill", function(d, i) { return z(i); });
	
	var total_links = 0;
	
	svg.selectAll("text")
        .data(layers)
        .enter()
        .append("text")
      .datum(function(d) { return {name: d.key, value: d.values[d.values.length - 1]}; })
		.attr("y", function(d) { return y(d.value.y0 + d.value.y / 2); })
		.attr("x", 885)
		.attr("font-size", "13px")
		.attr("style", "text-anchor: end")
		.text( function (d) { total_links = total_links + d.value.y;  return d.name + ", " + d.value.y; });

	  // Set the total link count in our text description of hte vis
	  d3.select('#darchive_count').text(total_links);
		
	  svg.append("g")
	      .attr("class", "x axis")
	      .attr("transform", "translate(0," + height + ")")
	      .call(xAxis);

	  svg.append("g")
	      .attr("class", "y axis")
	      .call(yAxis)
	    .append("text")
	      .attr("transform", "rotate(-90)")
	      .attr("y", 6)
	      .attr("dy", ".71em")
	      .style("text-anchor", "end")
	      .text("Links");
	
	});
}



var draw_storage_vis = function(){
    
	var format = d3.time.format.iso; //d3.time.format("%d-%b-%y").parse;
	
	var x = d3.time.scale()
	    .range([0, width]);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom");

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left");

	var line = d3.svg.line()
	    .x(function(d) { return x(d.date); })
	    .y(function(d) { return y(d.close); });

	var svg = d3.select("#storage-vis").append("svg")
        .attr("width", "100%")
        .attr('viewBox', '0 0 ' + String(width + margin.left + margin.right) + ' ' + String(height + margin.top + margin.bottom))
        .attr('perserveAspectRatio', 'none')
        .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.csv(stats_storage_url, function(error, data) {
	  data.forEach(function(d) {
	    d.date = format.parse(d.date);
	    d.close = +d.close;
	  });


	  // Super kludgy way to get latest size. TODO: improve.
	  var latest_size = 0;
	  x.domain(d3.extent(data, function(d) { return d.date; }));
	  y.domain(d3.extent(data, function(d) { latest_size = d.close; return d.close; }));

	  // Set the total size of store in our text description of the vis
	  d3.select('#total_size').text(latest_size);

	  svg.append("g")
	      .attr("class", "x axis")
	      .attr("transform", "translate(0," + height + ")")
	      .call(xAxis);

	  svg.append("g")
	      .attr("class", "y axis")
	      .call(yAxis)
	    .append("text")
	      .attr("transform", "rotate(-90)")
	      .attr("y", 6)
	      .attr("dy", ".71em")
	      .style("text-anchor", "end")
	      .text("GB of storage");

	  svg.append("path")
	      .datum(data)
	      .attr("class", "line")
	      .attr("d", line);
	});
}

draw_folks_vis();
draw_vesting_orgs_vis();
draw_registrar_vis();
draw_hits_vis();
draw_links_vis();
draw_darchive_vis();
draw_storage_vis();