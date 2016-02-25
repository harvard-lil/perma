function get_sum (link_data) {
		var sum = 0;
		for (i = 0; i < link_data.length; i++) {
			sum+=link_data[i].sum;
		}

		return sum;
	}

function draw_graph(p, link_data, vis_width, vis_height) {

		var total = 0;
		var x, y, size;
		var sum_of_all_sums = get_sum(link_data);

		p.strokeWeight(1);
		for (i = 0; i < vis_width; i+=4) {
			var x_t_1 = p.random(i-200, i+200);
			var x_t_2 = p.random(i-200, i+200);
			x = p.line(x_t_1, 0, x_t_2, vis_height);
		}

		p.strokeWeight(2);
		for (i = 0; i < vis_width; i+=8) {
			var x_t_1 = p.random(i-500, i+500);
			var x_t_2 = p.random(i-500, i+500);
			x = p.line(x_t_1, 0, x_t_2, vis_height);
		}

		/* Draw the top line of the area chart */
		total = 0;
		
		p.noFill();
		p.beginShape();
		for (i = 0; i < link_data.length; i++) {
			x = p.map(i, 0, link_data.length, 0, vis_width);
			y = p.map(total, 0, sum_of_all_sums, 0, vis_height);
			p.vertex(x, vis_height - y);
			total += link_data[i].sum;
		}
		p.vertex(vis_width, vis_height - y);
		p.endShape();

		total = 0;
		
		/* Draw a solid line at the bottom and right */
		
		p.strokeWeight(1);
		p.line(vis_width-1, vis_height - y, vis_width-1, vis_height);
		p.line(0, vis_height-1, vis_width, vis_height-1);


		/* Let's draw a big mask over the top of the graph 
		   so that the shape of the curve is obvious */
		p.fill(255);

		p.strokeWeight(0);
		p.beginShape();
		for (i = 0; i < link_data.length; i++) {
			x = p.map(i, 0, link_data.length, 0, vis_width);
			y = p.map(total, 0, sum_of_all_sums, 0, vis_height);
			p.vertex(x, vis_height - y);
			total += link_data[i].sum;
		}
		p.vertex(vis_width, vis_height - y);
		p.vertex(vis_width, 0);
		p.vertex(0, 0);
		
		p.endShape(p.CLOSE);

		/* Draw our labels */
		p.noStroke();
		p.fill(90);
		p.textSize(24);

		p.text(number_with_commas(total), vis_width - 130, 20);
		p.text(0, 0, vis_height-5);
	
}



var archives_vis = function( p ) {

	var link_data = [{"start": "2016-01-05", "sum": 3755, "end": "2016-01-12"}, {"start": "2015-12-29", "sum": 1588, "end": "2016-01-05"}, {"start": "2015-12-22", "sum": 1282, "end": "2015-12-29"}, {"start": "2015-12-15", "sum": 1807, "end": "2015-12-22"}, {"start": "2015-12-08", "sum": 1666, "end": "2015-12-15"}, {"start": "2015-12-01", "sum": 2741, "end": "2015-12-08"}, {"start": "2015-11-24", "sum": 2980, "end": "2015-12-01"}, {"start": "2015-11-17", "sum": 5072, "end": "2015-11-24"}, {"start": "2015-11-10", "sum": 10160, "end": "2015-11-17"}, {"start": "2015-11-03", "sum": 4919, "end": "2015-11-10"}, {"start": "2015-10-27", "sum": 5396, "end": "2015-11-03"}, {"start": "2015-10-20", "sum": 4448, "end": "2015-10-27"}, {"start": "2015-10-13", "sum": 6223, "end": "2015-10-20"}, {"start": "2015-10-06", "sum": 5413, "end": "2015-10-13"}, {"start": "2015-09-29", "sum": 5249, "end": "2015-10-06"}, {"start": "2015-09-22", "sum": 5228, "end": "2015-09-29"}, {"start": "2015-09-15", "sum": 4923, "end": "2015-09-22"}, {"start": "2015-09-08", "sum": 4145, "end": "2015-09-15"}, {"start": "2015-09-01", "sum": 3517, "end": "2015-09-08"}, {"start": "2015-08-25", "sum": 3083, "end": "2015-09-01"}, {"start": "2015-08-18", "sum": 2758, "end": "2015-08-25"}, {"start": "2015-08-11", "sum": 2203, "end": "2015-08-18"}, {"start": "2015-08-04", "sum": 2063, "end": "2015-08-11"}, {"start": "2015-07-28", "sum": 1349, "end": "2015-08-04"}, {"start": "2015-07-21", "sum": 948, "end": "2015-07-28"}, {"start": "2015-07-14", "sum": 1440, "end": "2015-07-21"}, {"start": "2015-07-07", "sum": 1466, "end": "2015-07-14"}, {"start": "2015-06-30", "sum": 826, "end": "2015-07-07"}, {"start": "2015-06-23", "sum": 1142, "end": "2015-06-30"}, {"start": "2015-06-16", "sum": 1316, "end": "2015-06-23"}, {"start": "2015-06-09", "sum": 1263, "end": "2015-06-16"}, {"start": "2015-06-02", "sum": 1586, "end": "2015-06-09"}, {"start": "2015-05-26", "sum": 1207, "end": "2015-06-02"}, {"start": "2015-05-19", "sum": 1193, "end": "2015-05-26"}, {"start": "2015-05-12", "sum": 1238, "end": "2015-05-19"}, {"start": "2015-05-05", "sum": 1075, "end": "2015-05-12"}, {"start": "2015-04-28", "sum": 904, "end": "2015-05-05"}, {"start": "2015-04-21", "sum": 2149, "end": "2015-04-28"}, {"start": "2015-04-14", "sum": 2331, "end": "2015-04-21"}, {"start": "2015-04-07", "sum": 2298, "end": "2015-04-14"}, {"start": "2015-03-31", "sum": 2461, "end": "2015-04-07"}, {"start": "2015-03-24", "sum": 2268, "end": "2015-03-31"}, {"start": "2015-03-17", "sum": 2481, "end": "2015-03-24"}, {"start": "2015-03-10", "sum": 1912, "end": "2015-03-17"}, {"start": "2015-03-03", "sum": 2733, "end": "2015-03-10"}, {"start": "2015-02-24", "sum": 1938, "end": "2015-03-03"}, {"start": "2015-02-17", "sum": 2654, "end": "2015-02-24"}, {"start": "2015-02-10", "sum": 2986, "end": "2015-02-17"}, {"start": "2015-02-03", "sum": 2543, "end": "2015-02-10"}, {"start": "2015-01-27", "sum": 1946, "end": "2015-02-03"}, {"start": "2015-01-20", "sum": 2972, "end": "2015-01-27"}, {"start": "2015-01-13", "sum": 2478, "end": "2015-01-20"}, {"start": "2015-01-06", "sum": 1831, "end": "2015-01-13"}, {"start": "2014-12-30", "sum": 952, "end": "2015-01-06"}, {"start": "2014-12-23", "sum": 915, "end": "2014-12-30"}, {"start": "2014-12-16", "sum": 1140, "end": "2014-12-23"}, {"start": "2014-12-09", "sum": 893, "end": "2014-12-16"}, {"start": "2014-12-02", "sum": 602, "end": "2014-12-09"}, {"start": "2014-11-25", "sum": 1150, "end": "2014-12-02"}, {"start": "2014-11-18", "sum": 2066, "end": "2014-11-25"}, {"start": "2014-11-11", "sum": 1709, "end": "2014-11-18"}, {"start": "2014-11-04", "sum": 1792, "end": "2014-11-11"}, {"start": "2014-10-28", "sum": 1851, "end": "2014-11-04"}, {"start": "2014-10-21", "sum": 2405, "end": "2014-10-28"}, {"start": "2014-10-14", "sum": 2369, "end": "2014-10-21"}, {"start": "2014-10-07", "sum": 2882, "end": "2014-10-14"}, {"start": "2014-09-30", "sum": 2151, "end": "2014-10-07"}, {"start": "2014-09-23", "sum": 2871, "end": "2014-09-30"}, {"start": "2014-09-16", "sum": 1932, "end": "2014-09-23"}, {"start": "2014-09-09", "sum": 1583, "end": "2014-09-16"}, {"start": "2014-09-02", "sum": 1838, "end": "2014-09-09"}, {"start": "2014-08-26", "sum": 1711, "end": "2014-09-02"}, {"start": "2014-08-19", "sum": 1194, "end": "2014-08-26"}, {"start": "2014-08-12", "sum": 479, "end": "2014-08-19"}, {"start": "2014-08-05", "sum": 525, "end": "2014-08-12"}, {"start": "2014-07-29", "sum": 563, "end": "2014-08-05"}, {"start": "2014-07-22", "sum": 332, "end": "2014-07-29"}, {"start": "2014-07-15", "sum": 264, "end": "2014-07-22"}, {"start": "2014-07-08", "sum": 460, "end": "2014-07-15"}, {"start": "2014-07-01", "sum": 275, "end": "2014-07-08"}, {"start": "2014-06-24", "sum": 151, "end": "2014-07-01"}, {"start": "2014-06-17", "sum": 226, "end": "2014-06-24"}, {"start": "2014-06-10", "sum": 245, "end": "2014-06-17"}, {"start": "2014-06-03", "sum": 302, "end": "2014-06-10"}, {"start": "2014-05-27", "sum": 123, "end": "2014-06-03"}, {"start": "2014-05-20", "sum": 366, "end": "2014-05-27"}, {"start": "2014-05-13", "sum": 514, "end": "2014-05-20"}, {"start": "2014-05-06", "sum": 584, "end": "2014-05-13"}, {"start": "2014-04-29", "sum": 330, "end": "2014-05-06"}, {"start": "2014-04-22", "sum": 492, "end": "2014-04-29"}, {"start": "2014-04-15", "sum": 596, "end": "2014-04-22"}, {"start": "2014-04-08", "sum": 983, "end": "2014-04-15"}, {"start": "2014-04-01", "sum": 963, "end": "2014-04-08"}, {"start": "2014-03-25", "sum": 1364, "end": "2014-04-01"}, {"start": "2014-03-18", "sum": 611, "end": "2014-03-25"}, {"start": "2014-03-11", "sum": 844, "end": "2014-03-18"}, {"start": "2014-03-04", "sum": 1182, "end": "2014-03-11"}, {"start": "2014-02-25", "sum": 613, "end": "2014-03-04"}, {"start": "2014-02-18", "sum": 1000, "end": "2014-02-25"}, {"start": "2014-02-11", "sum": 762, "end": "2014-02-18"}, {"start": "2014-02-04", "sum": 601, "end": "2014-02-11"}, {"start": "2014-01-28", "sum": 621, "end": "2014-02-04"}, {"start": "2014-01-21", "sum": 788, "end": "2014-01-28"}, {"start": "2014-01-14", "sum": 960, "end": "2014-01-21"}, {"start": "2014-01-07", "sum": 429, "end": "2014-01-14"}, {"start": "2013-12-31", "sum": 283, "end": "2014-01-07"}, {"start": "2013-12-24", "sum": 306, "end": "2013-12-31"}, {"start": "2013-12-17", "sum": 305, "end": "2013-12-24"}, {"start": "2013-12-10", "sum": 151, "end": "2013-12-17"}, {"start": "2013-12-03", "sum": 423, "end": "2013-12-10"}, {"start": "2013-11-26", "sum": 696, "end": "2013-12-03"}, {"start": "2013-11-19", "sum": 850, "end": "2013-11-26"}, {"start": "2013-11-12", "sum": 757, "end": "2013-11-19"}, {"start": "2013-11-05", "sum": 1276, "end": "2013-11-12"}, {"start": "2013-10-29", "sum": 610, "end": "2013-11-05"}, {"start": "2013-10-22", "sum": 1290, "end": "2013-10-29"}, {"start": "2013-10-15", "sum": 331, "end": "2013-10-22"}, {"start": "2013-10-08", "sum": 415, "end": "2013-10-15"}, {"start": "2013-10-01", "sum": 316, "end": "2013-10-08"}, {"start": "2013-09-24", "sum": 187, "end": "2013-10-01"}, {"start": "2013-09-17", "sum": 88, "end": "2013-09-24"}, {"start": "2013-09-10", "sum": 79, "end": "2013-09-17"}, {"start": "2013-09-03", "sum": 107, "end": "2013-09-10"}, {"start": "2013-08-27", "sum": 0, "end": "2013-09-03"}, {"start": "2013-08-20", "sum": 0, "end": "2013-08-27"}];
	link_data.reverse();

	var vis_width = 1200;
	var vis_height = 600;

	p.setup = function() {
		var archives_canvas = p.createCanvas(vis_width, vis_height);
		archives_canvas.parent('archives-vis-container');
		p.strokeCap(p.SQUARE);
		p.fill('#2D76EE');
		p.stroke('#2D76EE');
		p.background(250);
		p.noLoop();
	};

	p.draw = function() {
		draw_graph(p, link_data, vis_width, vis_height);
	};
};


new p5(archives_vis);



var users_vis = function( p ) {

	var link_data = [{"start": "2016-01-19", "sum": 87, "end": "2016-01-26"}, {"start": "2016-01-12", "sum": 64, "end": "2016-01-19"}, {"start": "2016-01-05", "sum": 133, "end": "2016-01-12"}, {"start": "2015-12-29", "sum": 50, "end": "2016-01-05"}, {"start": "2015-12-22", "sum": 24, "end": "2015-12-29"}, {"start": "2015-12-15", "sum": 111, "end": "2015-12-22"}, {"start": "2015-12-08", "sum": 18, "end": "2015-12-15"}, {"start": "2015-12-01", "sum": 37, "end": "2015-12-08"}, {"start": "2015-11-24", "sum": 71, "end": "2015-12-01"}, {"start": "2015-11-17", "sum": 61, "end": "2015-11-24"}, {"start": "2015-11-10", "sum": 99, "end": "2015-11-17"}, {"start": "2015-11-03", "sum": 55, "end": "2015-11-10"}, {"start": "2015-10-27", "sum": 93, "end": "2015-11-03"}, {"start": "2015-10-20", "sum": 122, "end": "2015-10-27"}, {"start": "2015-10-13", "sum": 106, "end": "2015-10-20"}, {"start": "2015-10-06", "sum": 88, "end": "2015-10-13"}, {"start": "2015-09-29", "sum": 173, "end": "2015-10-06"}, {"start": "2015-09-22", "sum": 113, "end": "2015-09-29"}, {"start": "2015-09-15", "sum": 199, "end": "2015-09-22"}, {"start": "2015-09-08", "sum": 153, "end": "2015-09-15"}, {"start": "2015-09-01", "sum": 234, "end": "2015-09-08"}, {"start": "2015-08-25", "sum": 233, "end": "2015-09-01"}, {"start": "2015-08-18", "sum": 237, "end": "2015-08-25"}, {"start": "2015-08-11", "sum": 155, "end": "2015-08-18"}, {"start": "2015-08-04", "sum": 29, "end": "2015-08-11"}, {"start": "2015-07-28", "sum": 53, "end": "2015-08-04"}, {"start": "2015-07-21", "sum": 44, "end": "2015-07-28"}, {"start": "2015-07-14", "sum": 51, "end": "2015-07-21"}, {"start": "2015-07-07", "sum": 97, "end": "2015-07-14"}, {"start": "2015-06-30", "sum": 17, "end": "2015-07-07"}, {"start": "2015-06-23", "sum": 30, "end": "2015-06-30"}, {"start": "2015-06-16", "sum": 37, "end": "2015-06-23"}, {"start": "2015-06-09", "sum": 22, "end": "2015-06-16"}, {"start": "2015-06-02", "sum": 38, "end": "2015-06-09"}, {"start": "2015-05-26", "sum": 43, "end": "2015-06-02"}, {"start": "2015-05-19", "sum": 33, "end": "2015-05-26"}, {"start": "2015-05-12", "sum": 48, "end": "2015-05-19"}, {"start": "2015-05-05", "sum": 57, "end": "2015-05-12"}, {"start": "2015-04-28", "sum": 50, "end": "2015-05-05"}, {"start": "2015-04-21", "sum": 52, "end": "2015-04-28"}, {"start": "2015-04-14", "sum": 29, "end": "2015-04-21"}, {"start": "2015-04-07", "sum": 50, "end": "2015-04-14"}, {"start": "2015-03-31", "sum": 25, "end": "2015-04-07"}, {"start": "2015-03-24", "sum": 50, "end": "2015-03-31"}, {"start": "2015-03-17", "sum": 75, "end": "2015-03-24"}, {"start": "2015-03-10", "sum": 61, "end": "2015-03-17"}, {"start": "2015-03-03", "sum": 47, "end": "2015-03-10"}, {"start": "2015-02-24", "sum": 59, "end": "2015-03-03"}, {"start": "2015-02-17", "sum": 61, "end": "2015-02-24"}, {"start": "2015-02-10", "sum": 75, "end": "2015-02-17"}, {"start": "2015-02-03", "sum": 112, "end": "2015-02-10"}, {"start": "2015-01-27", "sum": 124, "end": "2015-02-03"}, {"start": "2015-01-20", "sum": 161, "end": "2015-01-27"}, {"start": "2015-01-13", "sum": 22, "end": "2015-01-20"}, {"start": "2015-01-06", "sum": 28, "end": "2015-01-13"}, {"start": "2014-12-30", "sum": 26, "end": "2015-01-06"}, {"start": "2014-12-23", "sum": 3, "end": "2014-12-30"}, {"start": "2014-12-16", "sum": 14, "end": "2014-12-23"}, {"start": "2014-12-09", "sum": 22, "end": "2014-12-16"}, {"start": "2014-12-02", "sum": 18, "end": "2014-12-09"}, {"start": "2014-11-25", "sum": 20, "end": "2014-12-02"}, {"start": "2014-11-18", "sum": 37, "end": "2014-11-25"}, {"start": "2014-11-11", "sum": 26, "end": "2014-11-18"}, {"start": "2014-11-04", "sum": 55, "end": "2014-11-11"}, {"start": "2014-10-28", "sum": 138, "end": "2014-11-04"}, {"start": "2014-10-21", "sum": 67, "end": "2014-10-28"}, {"start": "2014-10-14", "sum": 129, "end": "2014-10-21"}, {"start": "2014-10-07", "sum": 51, "end": "2014-10-14"}, {"start": "2014-09-30", "sum": 37, "end": "2014-10-07"}, {"start": "2014-09-23", "sum": 65, "end": "2014-09-30"}, {"start": "2014-09-16", "sum": 64, "end": "2014-09-23"}, {"start": "2014-09-09", "sum": 45, "end": "2014-09-16"}, {"start": "2014-09-02", "sum": 51, "end": "2014-09-09"}, {"start": "2014-08-26", "sum": 38, "end": "2014-09-02"}, {"start": "2014-08-19", "sum": 173, "end": "2014-08-26"}, {"start": "2014-08-12", "sum": 80, "end": "2014-08-19"}, {"start": "2014-08-05", "sum": 14, "end": "2014-08-12"}, {"start": "2014-07-29", "sum": 5, "end": "2014-08-05"}, {"start": "2014-07-22", "sum": 8, "end": "2014-07-29"}, {"start": "2014-07-15", "sum": 10, "end": "2014-07-22"}, {"start": "2014-07-08", "sum": 6, "end": "2014-07-15"}, {"start": "2014-07-01", "sum": 9, "end": "2014-07-08"}, {"start": "2014-06-24", "sum": 10, "end": "2014-07-01"}, {"start": "2014-06-17", "sum": 10, "end": "2014-06-24"}, {"start": "2014-06-10", "sum": 14, "end": "2014-06-17"}, {"start": "2014-06-03", "sum": 11, "end": "2014-06-10"}, {"start": "2014-05-27", "sum": 21, "end": "2014-06-03"}, {"start": "2014-05-20", "sum": 15, "end": "2014-05-27"}, {"start": "2014-05-13", "sum": 15, "end": "2014-05-20"}, {"start": "2014-05-06", "sum": 17, "end": "2014-05-13"}, {"start": "2014-04-29", "sum": 23, "end": "2014-05-06"}, {"start": "2014-04-22", "sum": 26, "end": "2014-04-29"}, {"start": "2014-04-15", "sum": 19, "end": "2014-04-22"}, {"start": "2014-04-08", "sum": 27, "end": "2014-04-15"}, {"start": "2014-04-01", "sum": 40, "end": "2014-04-08"}, {"start": "2014-03-25", "sum": 57, "end": "2014-04-01"}, {"start": "2014-03-18", "sum": 23, "end": "2014-03-25"}, {"start": "2014-03-11", "sum": 14, "end": "2014-03-18"}, {"start": "2014-03-04", "sum": 26, "end": "2014-03-11"}, {"start": "2014-02-25", "sum": 16, "end": "2014-03-04"}, {"start": "2014-02-18", "sum": 20, "end": "2014-02-25"}, {"start": "2014-02-11", "sum": 35, "end": "2014-02-18"}, {"start": "2014-02-04", "sum": 31, "end": "2014-02-11"}, {"start": "2014-01-28", "sum": 32, "end": "2014-02-04"}, {"start": "2014-01-21", "sum": 19, "end": "2014-01-28"}, {"start": "2014-01-14", "sum": 29, "end": "2014-01-21"}, {"start": "2014-01-07", "sum": 34, "end": "2014-01-14"}, {"start": "2013-12-31", "sum": 6, "end": "2014-01-07"}, {"start": "2013-12-24", "sum": 10, "end": "2013-12-31"}, {"start": "2013-12-17", "sum": 18, "end": "2013-12-24"}, {"start": "2013-12-10", "sum": 14, "end": "2013-12-17"}, {"start": "2013-12-03", "sum": 25, "end": "2013-12-10"}, {"start": "2013-11-26", "sum": 29, "end": "2013-12-03"}, {"start": "2013-11-19", "sum": 34, "end": "2013-11-26"}, {"start": "2013-11-12", "sum": 44, "end": "2013-11-19"}, {"start": "2013-11-05", "sum": 75, "end": "2013-11-12"}, {"start": "2013-10-29", "sum": 177, "end": "2013-11-05"}, {"start": "2013-10-22", "sum": 512, "end": "2013-10-29"}, {"start": "2013-10-15", "sum": 183, "end": "2013-10-22"}, {"start": "2013-10-08", "sum": 289, "end": "2013-10-15"}, {"start": "2013-10-01", "sum": 167, "end": "2013-10-08"}, {"start": "2013-09-24", "sum": 33, "end": "2013-10-01"}, {"start": "2013-09-17", "sum": 51, "end": "2013-09-24"}, {"start": "2013-09-10", "sum": 36, "end": "2013-09-17"}, {"start": "2013-09-03", "sum": 22, "end": "2013-09-10"}, {"start": "2013-08-27", "sum": 0, "end": "2013-09-03"}, {"start": "2013-08-20", "sum": 0, "end": "2013-08-27"}];
	link_data.reverse();

	var vis_width = 1200;
	var vis_height = 600;

	  p.setup = function() {
		var archives_canvas = p.createCanvas(vis_width, vis_height);
		archives_canvas.parent('users-vis-container');
		p.strokeCap(p.SQUARE);
		p.fill('#2D76EE');
		p.stroke('#2D76EE');
		p.background(250);
		p.noLoop();
	};

	p.draw = function() {
		draw_graph(p, link_data, vis_width, vis_height);
	};
};

new p5(users_vis);


var today_vis = function( p ) {

	var height, width;

	var perma_api_archive_url = 'http://localhost:8000/service/stats/now/';

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
		    url: perma_api_archive_url,
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
			    p.stroke('#28e91a');
			    p.strokeWeight(2);
			    $(data['users']).each(function(i, time_of_creation) {
			      // Draw a line for each user in our list
					relative_x = p.map(time_of_creation, 0, 1440, 4, width - 4);
			      	p.line(relative_x, 8, relative_x, height - 42);
			    });

			    // Draw orgs
			    p.stroke('#fe52b6');
			    $(data['orgs']).each(function(i, time_of_creation) {
			      // Draw a line for each user in our list
			      	relative_x = p.map(time_of_creation, 0, 1440, 4, width - 4);
			      	p.line(relative_x, 8, relative_x, height - 42);
			    });

			    // Draw libs
			    p.stroke('#ef4923');
			    $(data['libraries']).each(function(i, time_of_creation) {
			      // Draw a line for each user in our list
			      	relative_x = p.map(time_of_creation, 0, 1440, 4, width - 4);
			      	p.line(relative_x, 8, relative_x, height - 42);
			    });

			    draw_scaffolding();
			}
		}); // End of ajax get
}

	function draw_scaffolding() {
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



function number_with_commas(x) {
	// Thanks, http://stackoverflow.com/a/2901298
	return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}