// House our sum data here. We should refactor this.
var sum_data;
var initial = true;

function get_numbers(field_key) {
	// Here we compute the sum, average, and latest week for the given field_key
	var sum = 0;
	for (i = 0; i < sum_data.length; i++) {
		sum+=sum_data[i][field_key];
	}

	var numbers = {'sum': sum,
		'average': Math.floor(sum/sum_data.length),
		'this_week': sum_data[sum_data.length-1][field_key]
	}

	return numbers;
}

function draw_graph(p, field_key, vis_width, vis_height) {
	// Our users and archives graph use the same logic we've gathered here.
	var total = 0;
	var x, y, size;
	var sum_of_all_sums = get_numbers(field_key).sum;
	var bottom_padding = 30;

	p.strokeWeight(1);
	for (i = 0; i < vis_width; i+=4) {
		var x_t_1 = p.random(i-200, i+200);
		var x_t_2 = p.random(i-200, i+200);
		x = p.line(x_t_1, 0, x_t_2, vis_height - bottom_padding);
	}

	p.strokeWeight(2);
	for (i = 0; i < vis_width; i+=8) {
		var x_t_1 = p.random(i-500, i+500);
		var x_t_2 = p.random(i-500, i+500);
		x = p.line(x_t_1, 0, x_t_2, vis_height - bottom_padding);
	}

	/* Draw the top line of the area chart */
	total = 0;

	p.noFill();
	p.beginShape();
	for (i = 0; i < sum_data.length; i++) {
		x = p.map(i, 0, sum_data.length, 0, vis_width);
		y = p.map(total, 0, sum_of_all_sums, 0, vis_height - bottom_padding);
		p.vertex(x, vis_height - y);
		total += sum_data[i][field_key];
	}
	p.vertex(vis_width, vis_height - y);
	p.endShape();

	total = 0;

	/* Draw a solid line at the bottom and right */
	p.strokeWeight(1);
	p.line(vis_width-1, vis_height - y, vis_width-1, vis_height - bottom_padding);
	p.line(0, vis_height-1 - bottom_padding, vis_width, vis_height-1 - bottom_padding);


	/* Let's draw a big mask over the top of the graph 
	so that the shape of the curve is obvious */
	p.fill(255);

	p.strokeWeight(0);
	p.beginShape();
	for (i = 0; i < sum_data.length; i++) {
		x = p.map(i, 0, sum_data.length, 0, vis_width);
		y = p.map(total, 0, sum_of_all_sums, 0, vis_height - bottom_padding);
		p.vertex(x, vis_height - y);
		total += sum_data[i][field_key];
	}
	p.vertex(vis_width, vis_height - y);
	p.vertex(vis_width, 0);
	p.vertex(0, 0);

	p.endShape(p.CLOSE);

	/* Draw our labels */
	p.noStroke();
	p.fill(90);
	p.textSize(24);

	p.text('June 2013', 0, vis_height-5);
	p.text('today', vis_width-60, vis_height-5);
}


var archives_vis = function(p) {
	// Create the archives vis here
	var vis_width = 1200;
	var vis_height = 600;

	p.setup = function() {
		var archives_canvas = p.createCanvas(vis_width, vis_height);
		archives_canvas.parent('archives-vis-container');
		p.strokeCap(p.SQUARE);
		p.fill('#2D76EE');
		p.stroke('#2D76EE');
		p.noLoop();
	};

	p.draw = function() {
		draw_graph(p, 'links_sum', vis_width, vis_height);
	};
};


var users_vis = function( p ) {
	// Create the users vis here
	var vis_width = 1200;
	var vis_height = 600;

	p.setup = function() {
		var archives_canvas = p.createCanvas(vis_width, vis_height);
		archives_canvas.parent('users-vis-container');
		p.strokeCap(p.SQUARE);
		p.fill('#2D76EE');
		p.stroke('#2D76EE');
		p.noLoop();
};

	p.draw = function() {
		draw_graph(p, 'users_sum', vis_width, vis_height);
	};
};


var draw_weekly = function(initial) {
	// Create graphs and update counts
	var url = '/service/stats/sums/';
	$.ajax({
		type: 'GET',
		dataType: "json",
		url: url,
		success: function(response_data) {
			// Draw our two sum-based visualizations
			// Oh, this is so klunky (yes, with a k)
			if (initial) {
				sum_data = response_data;
				var uv = new p5(users_vis);
				var av = new p5(archives_vis);
			}

			// Update our counts
			$('#archives_sum_container').html(get_numbers('links_sum').sum);
			$('#archives_average_container').html(get_numbers('links_sum').average);
			$('#archives_latest_container').html(get_numbers('links_sum').this_week);

			$('#users_sum_container').html(get_numbers('users_sum').sum);
			$('#users_average_container').html(get_numbers('users_sum').average);
			$('#users_latest_container').html(get_numbers('users_sum').this_week);

			$('#org_sum_container').html(get_numbers('organizations_sum').sum);
			$('#orgs_average_container').html(get_numbers('organizations_sum').average);
			$('#orgs_latest_container').html(get_numbers('organizations_sum').this_week);

			$('#libraries_sum_container').html(get_numbers('registrars_sum').sum);
			$('#libraries_average_container').html(get_numbers('registrars_sum').average);
			$('#libraries_latest_container').html(get_numbers('registrars_sum').this_week);
		}
	}); // End of ajax get
}


var today_vis = function( p ) {
	var height, width;
	var url = '/service/stats/now/';

	p.setup = function() {
		width = 1200;
		height = 270;

		// Our timestamps are the second of the day. 1440 seconds per day.
		var canvas = p.createCanvas(width, height);
		canvas.parent('today-vis-container');
		p.background('#f7f7f7');

		p.stroke(255);

		p.strokeWeight(1);
		p.strokeCap(p.SQUARE);
		p.noLoop();
	};

	p.draw = function() {
		draw_events();
		window.setInterval(draw_events, 60000);
	};

	function draw_events() {
		$.ajax({
			type: 'GET',
			dataType: "json",
			url: url,
			success: function(data) {

			p.clear();
			p.background(255);

			var relative_x = 0;

			// Draw links
			p.stroke('#2D76EE');
			p.strokeWeight(1);
			$(data['links']).each(function(i, time_of_creation) {
				relative_x = p.map(time_of_creation, 0, 1440, 4, width - 4);
				p.line(relative_x, 8, relative_x, height - 42);
			});

			// Draw users
			p.stroke('#77AE3A');
			p.strokeWeight(2);
			$(data['users']).each(function(i, time_of_creation) {
				// Draw a line for each user in our list
				relative_x = p.map(time_of_creation, 0, 1440, 4, width - 4);
				p.line(relative_x, 8, relative_x, height - 42);
			});

			// Draw orgs
			p.stroke('#DD671A');
			$(data['organizations']).each(function(i, time_of_creation) {
				// Draw a line for each user in our list
				relative_x = p.map(time_of_creation, 0, 1440, 4, width - 4);
				p.line(relative_x, 8, relative_x, height - 42);
			});

			// Draw libs
			p.stroke('#F14FBC');
			$(data['registrars']).each(function(i, time_of_creation) {
				// Draw a line for each user in our list
				relative_x = p.map(time_of_creation, 0, 1440, 4, width - 4);
				p.line(relative_x, 8, relative_x, height - 42);
			});

			draw_scaffolding();

			// update legend
			if ($('#legend_archives .num_value').length === 0 ||
				data['links'].length != $('.legend-archives .num_value').html() ||
				data['users'].length != $('.legend-users .num_value').html() ||
				data['organizations'].length != $('.legend-orgs .num_value').html() ||
				data['registrars'].length != $('.legend-libraries .num_value').html()) {

					// Such a kludge. fix.
					draw_weekly(initial);
					initial = false;

					$('.legend-archives .num-value').html(data['links'].length);
					$('.legend-users .num-value').html(data['users'].length);
					$('.legend-orgs .num-value').html(data['organizations'].length);
					$('.legend-libraries .num-value').html(data['registrars'].length);


					// Hide our legend bits if they have 0 events today
					// This whole thing is kludgy. refactor.
					if (data['links'].length === 0) {
						$('.legend-archives').hide();
					} else if (data['links'].length === 1) {
						$('.legend-archives .num-label').html('archive');
						$('.legend-archives').show();
					} else {
						$('.legend-archives .num-label').html('archives');
						$('.legend-archives').show();
					}

					if (data['users'].length === 0) {
						$('.legend-users').hide();
					} else if (data['users'].length === 1) {
						$('.legend-users .num-label').html('user');
						$('.legend-users').show();
					} else {
						$('.legend-users .num-label').html('users');
						$('.legend-users').show();
					}

					if (data['organizations'].length === 0) {
						$('.legend-orgs').hide();
					} else if (data['organizations'].length === 1) {
						$('.legend-orgs .num-label').html('organization');
						$('.legend-orgs').show();
					} else {
						$('.legend-orgs .num-label').html('organizations');
						$('.legend-orgs').show();
					}

					if (data['registrars'].length === 0) {
						$('.legend-libraries').hide();
					} else if (data['registrars'].length === 1) {
						$('.legend-libraries .num-label').html('library');
						$('.legend-libraries').show();
					} else {
						$('.legend-libraries .num-label').html('libraries');
						$('.legend-libraries').show();
					}
				}
			} // end if we notice a change in stats
		}); // End of ajax get
	}

	function draw_scaffolding() {
		// Draw our ticks and and our labels
		p.strokeWeight(1);
		p.stroke(150);
		p.line(4, height - 20, 4, height - 36); // left tick
		p.line(width - 4, height - 20, width - 4, height - 36);  // right tick
		p.line(4, height - 28, width - 4, height - 28); // long, base line

		var m = moment();
		current_minute = m.hour() * 60 + m.minute();
		var x_of_current_time = p.map(current_minute, 0, 1440, 0, width);
		p.line(x_of_current_time, height - 20, x_of_current_time, height - 36);  // clock tick

		p.textSize(18);
		p.fill(90);
		p.strokeWeight(0);
		p.text('new day', 6, height - 7);
		p.text('now', x_of_current_time - 13 , height - 7);
		p.text('midnight', width - 75, height - 7);
	}
};

new p5(today_vis);