var archives_vis = function( p ) {

	var link_data = [{"start": "2016-01-05", "sum": 3755, "end": "2016-01-12"}, {"start": "2015-12-29", "sum": 1588, "end": "2016-01-05"}, {"start": "2015-12-22", "sum": 1282, "end": "2015-12-29"}, {"start": "2015-12-15", "sum": 1807, "end": "2015-12-22"}, {"start": "2015-12-08", "sum": 1666, "end": "2015-12-15"}, {"start": "2015-12-01", "sum": 2741, "end": "2015-12-08"}, {"start": "2015-11-24", "sum": 2980, "end": "2015-12-01"}, {"start": "2015-11-17", "sum": 5072, "end": "2015-11-24"}, {"start": "2015-11-10", "sum": 10160, "end": "2015-11-17"}, {"start": "2015-11-03", "sum": 4919, "end": "2015-11-10"}, {"start": "2015-10-27", "sum": 5396, "end": "2015-11-03"}, {"start": "2015-10-20", "sum": 4448, "end": "2015-10-27"}, {"start": "2015-10-13", "sum": 6223, "end": "2015-10-20"}, {"start": "2015-10-06", "sum": 5413, "end": "2015-10-13"}, {"start": "2015-09-29", "sum": 5249, "end": "2015-10-06"}, {"start": "2015-09-22", "sum": 5228, "end": "2015-09-29"}, {"start": "2015-09-15", "sum": 4923, "end": "2015-09-22"}, {"start": "2015-09-08", "sum": 4145, "end": "2015-09-15"}, {"start": "2015-09-01", "sum": 3517, "end": "2015-09-08"}, {"start": "2015-08-25", "sum": 3083, "end": "2015-09-01"}, {"start": "2015-08-18", "sum": 2758, "end": "2015-08-25"}, {"start": "2015-08-11", "sum": 2203, "end": "2015-08-18"}, {"start": "2015-08-04", "sum": 2063, "end": "2015-08-11"}, {"start": "2015-07-28", "sum": 1349, "end": "2015-08-04"}, {"start": "2015-07-21", "sum": 948, "end": "2015-07-28"}, {"start": "2015-07-14", "sum": 1440, "end": "2015-07-21"}, {"start": "2015-07-07", "sum": 1466, "end": "2015-07-14"}, {"start": "2015-06-30", "sum": 826, "end": "2015-07-07"}, {"start": "2015-06-23", "sum": 1142, "end": "2015-06-30"}, {"start": "2015-06-16", "sum": 1316, "end": "2015-06-23"}, {"start": "2015-06-09", "sum": 1263, "end": "2015-06-16"}, {"start": "2015-06-02", "sum": 1586, "end": "2015-06-09"}, {"start": "2015-05-26", "sum": 1207, "end": "2015-06-02"}, {"start": "2015-05-19", "sum": 1193, "end": "2015-05-26"}, {"start": "2015-05-12", "sum": 1238, "end": "2015-05-19"}, {"start": "2015-05-05", "sum": 1075, "end": "2015-05-12"}, {"start": "2015-04-28", "sum": 904, "end": "2015-05-05"}, {"start": "2015-04-21", "sum": 2149, "end": "2015-04-28"}, {"start": "2015-04-14", "sum": 2331, "end": "2015-04-21"}, {"start": "2015-04-07", "sum": 2298, "end": "2015-04-14"}, {"start": "2015-03-31", "sum": 2461, "end": "2015-04-07"}, {"start": "2015-03-24", "sum": 2268, "end": "2015-03-31"}, {"start": "2015-03-17", "sum": 2481, "end": "2015-03-24"}, {"start": "2015-03-10", "sum": 1912, "end": "2015-03-17"}, {"start": "2015-03-03", "sum": 2733, "end": "2015-03-10"}, {"start": "2015-02-24", "sum": 1938, "end": "2015-03-03"}, {"start": "2015-02-17", "sum": 2654, "end": "2015-02-24"}, {"start": "2015-02-10", "sum": 2986, "end": "2015-02-17"}, {"start": "2015-02-03", "sum": 2543, "end": "2015-02-10"}, {"start": "2015-01-27", "sum": 1946, "end": "2015-02-03"}, {"start": "2015-01-20", "sum": 2972, "end": "2015-01-27"}, {"start": "2015-01-13", "sum": 2478, "end": "2015-01-20"}, {"start": "2015-01-06", "sum": 1831, "end": "2015-01-13"}, {"start": "2014-12-30", "sum": 952, "end": "2015-01-06"}, {"start": "2014-12-23", "sum": 915, "end": "2014-12-30"}, {"start": "2014-12-16", "sum": 1140, "end": "2014-12-23"}, {"start": "2014-12-09", "sum": 893, "end": "2014-12-16"}, {"start": "2014-12-02", "sum": 602, "end": "2014-12-09"}, {"start": "2014-11-25", "sum": 1150, "end": "2014-12-02"}, {"start": "2014-11-18", "sum": 2066, "end": "2014-11-25"}, {"start": "2014-11-11", "sum": 1709, "end": "2014-11-18"}, {"start": "2014-11-04", "sum": 1792, "end": "2014-11-11"}, {"start": "2014-10-28", "sum": 1851, "end": "2014-11-04"}, {"start": "2014-10-21", "sum": 2405, "end": "2014-10-28"}, {"start": "2014-10-14", "sum": 2369, "end": "2014-10-21"}, {"start": "2014-10-07", "sum": 2882, "end": "2014-10-14"}, {"start": "2014-09-30", "sum": 2151, "end": "2014-10-07"}, {"start": "2014-09-23", "sum": 2871, "end": "2014-09-30"}, {"start": "2014-09-16", "sum": 1932, "end": "2014-09-23"}, {"start": "2014-09-09", "sum": 1583, "end": "2014-09-16"}, {"start": "2014-09-02", "sum": 1838, "end": "2014-09-09"}, {"start": "2014-08-26", "sum": 1711, "end": "2014-09-02"}, {"start": "2014-08-19", "sum": 1194, "end": "2014-08-26"}, {"start": "2014-08-12", "sum": 479, "end": "2014-08-19"}, {"start": "2014-08-05", "sum": 525, "end": "2014-08-12"}, {"start": "2014-07-29", "sum": 563, "end": "2014-08-05"}, {"start": "2014-07-22", "sum": 332, "end": "2014-07-29"}, {"start": "2014-07-15", "sum": 264, "end": "2014-07-22"}, {"start": "2014-07-08", "sum": 460, "end": "2014-07-15"}, {"start": "2014-07-01", "sum": 275, "end": "2014-07-08"}, {"start": "2014-06-24", "sum": 151, "end": "2014-07-01"}, {"start": "2014-06-17", "sum": 226, "end": "2014-06-24"}, {"start": "2014-06-10", "sum": 245, "end": "2014-06-17"}, {"start": "2014-06-03", "sum": 302, "end": "2014-06-10"}, {"start": "2014-05-27", "sum": 123, "end": "2014-06-03"}, {"start": "2014-05-20", "sum": 366, "end": "2014-05-27"}, {"start": "2014-05-13", "sum": 514, "end": "2014-05-20"}, {"start": "2014-05-06", "sum": 584, "end": "2014-05-13"}, {"start": "2014-04-29", "sum": 330, "end": "2014-05-06"}, {"start": "2014-04-22", "sum": 492, "end": "2014-04-29"}, {"start": "2014-04-15", "sum": 596, "end": "2014-04-22"}, {"start": "2014-04-08", "sum": 983, "end": "2014-04-15"}, {"start": "2014-04-01", "sum": 963, "end": "2014-04-08"}, {"start": "2014-03-25", "sum": 1364, "end": "2014-04-01"}, {"start": "2014-03-18", "sum": 611, "end": "2014-03-25"}, {"start": "2014-03-11", "sum": 844, "end": "2014-03-18"}, {"start": "2014-03-04", "sum": 1182, "end": "2014-03-11"}, {"start": "2014-02-25", "sum": 613, "end": "2014-03-04"}, {"start": "2014-02-18", "sum": 1000, "end": "2014-02-25"}, {"start": "2014-02-11", "sum": 762, "end": "2014-02-18"}, {"start": "2014-02-04", "sum": 601, "end": "2014-02-11"}, {"start": "2014-01-28", "sum": 621, "end": "2014-02-04"}, {"start": "2014-01-21", "sum": 788, "end": "2014-01-28"}, {"start": "2014-01-14", "sum": 960, "end": "2014-01-21"}, {"start": "2014-01-07", "sum": 429, "end": "2014-01-14"}, {"start": "2013-12-31", "sum": 283, "end": "2014-01-07"}, {"start": "2013-12-24", "sum": 306, "end": "2013-12-31"}, {"start": "2013-12-17", "sum": 305, "end": "2013-12-24"}, {"start": "2013-12-10", "sum": 151, "end": "2013-12-17"}, {"start": "2013-12-03", "sum": 423, "end": "2013-12-10"}, {"start": "2013-11-26", "sum": 696, "end": "2013-12-03"}, {"start": "2013-11-19", "sum": 850, "end": "2013-11-26"}, {"start": "2013-11-12", "sum": 757, "end": "2013-11-19"}, {"start": "2013-11-05", "sum": 1276, "end": "2013-11-12"}, {"start": "2013-10-29", "sum": 610, "end": "2013-11-05"}, {"start": "2013-10-22", "sum": 1290, "end": "2013-10-29"}, {"start": "2013-10-15", "sum": 331, "end": "2013-10-22"}, {"start": "2013-10-08", "sum": 415, "end": "2013-10-15"}, {"start": "2013-10-01", "sum": 316, "end": "2013-10-08"}, {"start": "2013-09-24", "sum": 187, "end": "2013-10-01"}, {"start": "2013-09-17", "sum": 88, "end": "2013-09-24"}, {"start": "2013-09-10", "sum": 79, "end": "2013-09-17"}, {"start": "2013-09-03", "sum": 107, "end": "2013-09-10"}, {"start": "2013-08-27", "sum": 0, "end": "2013-09-03"}, {"start": "2013-08-20", "sum": 0, "end": "2013-08-27"}];
	link_data.reverse();

	var vis_width = 1200;
	var vis_height = 600;

	  var x = 100; 
	  var y = 100;

	  p.setup = function() {
		var archives_canvas = p.createCanvas(vis_width, vis_height);
		archives_canvas.parent('archives-vis-container');
		p.strokeCap(p.ROUND);
		p.fill('#2D76EE');
		p.stroke('#2D76EE');
		p.noLoop();
	};

	  p.draw = function() {

		var total = 0;
		var x = 0;
		var y, size;
		var sum_of_all_sums = get_sum();

		for (i = 0; i < link_data.length; i++) {
			p.strokeWeight(2);
			x = p.map(i, 0, link_data.length, 0, vis_width);
			x2 = p.map(i + p.floor(p.random(1,22)), 0, link_data.length, 0, vis_width);
			x3 = p.map(i + p.floor(p.random(1,22)), 0, link_data.length, 0, vis_width);
			x4 = p.map(i - p.floor(p.random(1,22)), 0, link_data.length, 0, vis_width);
			x5 = p.map(i + p.floor(p.random(1,22)), 0, link_data.length, 0, vis_width);
			
			y = p.map(total, 0, sum_of_all_sums, 0, vis_height);

			/* Draw a hevier line for each sub */
			p.line(x, vis_height - y, x2, vis_height);

			/* And a few lighter ones */
			p.strokeWeight(1);
			p.line(x, vis_height - y, x3, vis_height);
			p.line(x, vis_height - y, x4, vis_height);
			p.line(x, vis_height - y, x5, vis_height);
			
			total += link_data[i].sum;
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


		/* Draw a solid line at the bottom and right */
		p.stroke('#88cfff');
		p.strokeWeight(3);
		p.line(vis_width-1, vis_height - y, vis_width-1, vis_height);
		p.line(0, vis_height-1, vis_width, vis_height-1);



		/*p.noStroke();
		p.fill(90);
		p.textSize(20);
		p.text(sum_of_all_sums, 0, 30);
		p.text(sum_of_all_sums/2, 0, vis_height/2);
		p.text(0, 0, vis_height-20);

		p.text('May 2013', 30, vis_height-10);
		p.text('this week', vis_width - 160, vis_height-10);*/
	  };

	function get_sum () {
		var sum = 0;
		for (i = 0; i < link_data.length; i++) {
			sum+=link_data[i].sum;
		}

		return sum;
	}
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
		p.background('#f7f7f7');
		p.strokeCap(p.ROUND);
		p.fill('#2D76EE');
		p.stroke('#2D76EE');
		p.noLoop();
	};

	  p.draw = function() {

		var total = 0;
		var x = 0;
		var y, size;
		var sum_of_all_sums = get_sum();

		function get_min(start_num) {

			var l = start_num - 44;
			var u = start_num + 44;

			if (l < 0) {
				l = 0;
			}

			if (u > link_data) {
				u = link_data;
			}

			return p.floor(p.random(l, u));
		}

		for (i = 0; i < link_data.length; i++) {
			p.strokeWeight(2);
			x = p.map(i, 0, link_data.length, 0, vis_width);
			y = p.map(total, 0, sum_of_all_sums-60, 0, vis_height);
			x2 = p.map(get_min(i), 0, link_data.length, 0, vis_width);

			/* Draw a hevier line for each sub */
			p.line(x, vis_height - y, x2, vis_height);

			/* And a few lighter ones */
			p.strokeWeight(1);

			for (light_line_index = 0; light_line_index < 3; light_line_index++) {
				var x_light = p.map(get_min(i), 0, link_data.length, 0, vis_width);
				p.line(x, vis_height - y, x_light, vis_height);
			}

			
			total += link_data[i].sum;
		}


		//for (i = 0; i < link_data.length; i++) {
		//	p.strokeWeight(2);
		//	x = p.map(i, 0, link_data.length, 0, vis_width);
		//	y = p.map(total, 0, sum_of_all_sums-60, 0, vis_height);
		//	var x2 = p.map(get_min(i), 0, link_data.length, 0, vis_width);

			/* Draw a hevier line for each point*/
		//	p.line(x, vis_height - y, x2, vis_height);

			/* And a few lighter ones */
		//	p.strokeWeight(1);
		//	for (light_line_index = 10; light_line_index < 10; light_line_index++) {
		//		var x_light = p.map(get_min(i), 0, link_data.length, 0, vis_width);
		//		p.line(x, vis_height - y, x_light, vis_height);
		//	}

		//	total += link_data[i].sum;
		//}








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
		p.stroke('#6c9ff3');
		p.strokeWeight(1);
		p.line(vis_width-1, vis_height - y, vis_width-1, vis_height);
		p.line(0, vis_height-1, vis_width, vis_height-1);


		/* Some of our lines in our graph go a little wild
		   let's draw a big mask over the top of the graph
		   to hide any weirdness */
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
		p.textSize(20);

		p.text(total, vis_width - 80, 20);
		p.text(0, 0, vis_height-5);
		

	  };

	function get_sum () {
		var sum = 0;
		for (i = 0; i < link_data.length; i++) {
			sum+=link_data[i].sum;
		}

		return sum;
	}
};

new p5(users_vis);













var today_vis = function( p ) {



var left_margin;
var height, width;
var yestrday_archives, today_archives = [];
var yestrday_users, today_users = [];
var yestrday_archives, archives, users, orgs, libraries = [];
var minute, hour, last_minute_of_day, padding, ratio;

var perma_api_archive_url = 'https://api.perma.cc/v1/public/archives/';



	  p.setup = function() {
		
	padding = 6;

	width = window.innerWidth * .8 + 2 * padding;
	height = window.innerHeight * .4;

	// Our timestamps are the second of the day. 1440 seconds per day.
	ratio =  width/1440;

	var canvas = p.createCanvas(width, height);
	canvas.parent('today-vis-container');
	p.background('#f7f7f7');

	p.stroke(255);
  
  	p.strokeWeight(1);
	p.strokeCap(p.SQUARE);

	left_margin = 20;

	yesterday_archives = [1334, 1020, 943, 852, 1324, 750, 735, 21, 821, 1118, 953, 916, 1328, 119, 672, 1270, 9, 790, 1097, 1362, 703, 720, 972, 822, 549, 974, 774, 1141, 294, 1077, 1103, 283, 622, 577, 695, 1242, 61, 955, 392, 1355, 1157, 1344, 968, 1135, 551, 1206, 4, 1350, 158, 806, 555, 687, 1242, 802, 1082, 550, 1135, 487, 308, 1167, 1013, 776, 525, 877, 513, 425, 1062, 1135, 941, 957, 52, 779, 1330, 451, 53, 629, 766, 1085, 543, 796, 1289, 575, 1130, 770, 282, 800, 62, 669, 881, 1058, 29, 415, 1135, 870, 721, 1015, 137, 1195, 38, 1082, 1001, 1366, 141, 1057, 925, 1069, 1037, 913, 1366, 1369, 1008, 874, 720, 1225, 619, 939, 1171, 894, 568, 1130, 1335, 905, 1032, 1360, 802, 861, 743, 122, 71, 1127, 1223, 50, 1262, 1055, 127, 804, 219, 150, 100, 1307, 979, 811, 708, 128, 736, 919, 924, 1295, 763, 1183, 1300, 1253, 68, 4, 860, 849, 747, 1338, 649, 1002, 1439, 1324, 248, 1001, 1039, 1229, 1356, 1433, 1281, 1038, 1267, 872, 1324, 1, 1297, 1315, 1274, 98, 528, 980, 1099, 1004, 999, 1350, 883, 944, 748, 1290, 12, 435, 566, 559, 715, 897, 1257, 1360, 32, 662, 1400, 499, 659, 617, 1163, 123, 24, 1304, 803, 586, 982, 968, 1277, 984, 1435, 779, 15, 1310, 741, 982, 1291, 1034, 729, 1024, 1183, 1146, 575, 772, 1328, 840, 492, 1326, 999, 1340, 1135, 1144, 425, 1195, 1439, 123, 1052, 1331, 1317, 771, 928, 56, 825, 1079, 133, 955, 1052, 1402, 870, 1422, 1042, 818, 111, 1039, 1366, 646, 1048, 1268, 1344, 1431, 614, 649, 1278, 106, 236, 983, 1186, 1327, 1334, 292, 184, 1355, 515, 987, 942, 711, 1239, 797, 705, 1035, 761, 761, 1041, 430, 909, 1135, 651, 1031, 1271, 1024, 469, 141, 904, 1290, 821, 1378, 1062, 1025, 31, 887, 79, 952, 65, 1098, 1109, 581, 1038, 790, 929, 646, 122, 969, 877, 1324, 866, 768, 10, 1029, 721, 848, 951, 1036, 13, 924, 1035, 686, 983, 1101, 783, 1319, 1077, 877, 492, 1018, 798, 1341, 913, 1103, 1291, 1398, 970, 1437, 1300, 1138, 566, 918, 995, 125, 1331, 1303, 979, 1259, 1234, 963, 1265, 906, 1307, 943, 982, 760, 1382, 816, 160, 979, 1322, 1302, 911, 147, 1288, 1314, 1083, 1209, 987, 1302, 1295, 1355, 1339, 1438, 1425, 1180, 1246, 1277, 951, 1395, 849, 117, 1085, 705, 114, 518, 1428, 731, 50, 688, 1357, 99, 1340, 1, 1095, 19, 1389, 37, 732, 1290, 1367, 568, 842, 757, 805, 931, 1118, 620, 68, 52, 857, 1077, 92, 200, 993, 207, 875, 918, 1199, 565, 1264, 1272, 553, 563, 544, 1073, 1274, 1245, 553, 874, 861, 910, 1314, 642, 889, 1127, 552, 786, 1378, 44, 844, 943, 546, 119, 772, 1428, 930, 1322, 241, 126, 1024, 581, 1338, 540, 149, 1136, 1327, 1055, 1045, 1079, 776, 1435, 506, 1319, 1161, 934, 1419, 590, 1134, 665, 1268, 5, 844, 939, 585, 83, 639, 272, 1409, 1353, 86, 1236, 1022, 593, 1342, 1096, 1218, 1153, 600, 1432, 23, 1239, 520, 128, 585, 1432, 963, 868, 584, 48, 0, 38, 957, 588, 1379, 55, 1277, 1344, 1351, 646, 1349, 854, 1114, 1046, 1289, 1116, 18, 667, 1296, 1368, 1278, 849, 1035, 56, 1310, 399, 148, 538, 1340, 1327, 1250, 855, 1128, 1391, 1036, 919, 15, 1253, 936, 610, 22, 1333, 283, 1436, 787, 1135, 1356, 74, 122, 865, 940, 1295, 253, 1250, 730, 884, 46, 1336, 911, 16, 562, 876, 33, 1333, 1337, 559, 1267, 1352, 1389, 1295, 970, 874, 330, 1089, 728, 762, 1114, 1302, 543, 1336, 725, 138, 167, 107, 1073, 1313, 1127, 1051, 1103, 1319, 1181, 986, 655, 1005, 1160, 860, 38, 1047, 981, 1280];
	today_archives = [294, 577, 551, 630, 158, 555, 550, 487, 525, 513, 425, 282, 137, 38, 141, 127, 219, 150, 128, 68, 649, 248, 98, 528, 12, 435, 559, 32, 659, 617, 586, 15, 575, 492, 123, 56, 614, 236, 292, 184, 651, 608, 469, 141, 31, 646, 122, 624, 566, 125, 160, 147, 117, 518, 50, 1, 37, 68, 200, 565, 563, 552, 633, 119, 241, 126, 506, 5, 83, 639, 272, 128, 585, 48, 0, 38, 588, 55, 18, 399, 538, 15, 610, 22, 283, 122, 253, 46, 16, 33, 543, 138, 167, 655, 38];
	archives = [];
	//archives = archives.concat(yesterday_archives);
	archives = archives.concat(today_archives);

	users = [];
	yesterday_users = [630, 502, 700, 201, 100, 470, 890, 933, 1102];
	today_users = [201, 100, 470, 508];
	users = users.concat(today_users);

	orgs = [572];
	libraries = [];

	var now = new Date();
	last_minute_of_day = now.getHours() * 60 + now.getMinutes();



	draw_scaffolding();
	draw_archive();
	};

	  p.draw = function() {

			var now = new Date();
	current_minute = now.getHours() * 60 + now.getMinutes();

	if (last_minute_of_day !== current_minute) {
		last_minute_of_day = current_minute;

		draw_archive();
	}

	  };

	function draw_archive() {


	$.ajax({
		type: 'GET',
    	crossDomain: true,
		dataType: "jsonp",
	    url: perma_api_archive_url,
	    success: function(data) {

			$(data['objects']).each(function(i, val) {
				// Let's draw our archives

				// Some nastiness to turn the timestamp into a Date object
				var t = val["creation_timestamp"].replace(/T/g , " ").split(/[- :]/);
				var d = new Date(t[0], t[1]-1, t[2], t[3], t[4], t[5]);
				var minute_of_day_of_archive = d.getMinutes();
				minute_of_day_of_archive += d.getHours() * 60;

				// We've converted our archive into a minute. add it to the list.
				if (archives.indexOf(minute_of_day_of_archive) === -1){
					archives.push(minute_of_day_of_archive);
				}
			});

			// Draw archives
			p.stroke('#2D76EE');
			p.strokeWeight(1);
		    $(archives).each(function(i, time_of_creation) {
		      p.line(ratio * time_of_creation + padding, .05 * height, ratio * time_of_creation + padding, .90 * height);
		    });

		    // Draw users
		    p.stroke('#28e91a');
		    p.strokeWeight(2);
		    $(users).each(function(i, time_of_creation) {
		      // Draw a line for each user in our list
		      p.line(ratio * time_of_creation + padding, .05 * height, ratio * time_of_creation + padding, .90 * height);
		    });

		    // Draw orgs
		    p.stroke('#fe52b6');
		    $(orgs).each(function(i, time_of_creation) {
		      // Draw a line for each user in our list
		      p.line(ratio * time_of_creation + padding, .05 * height, ratio * time_of_creation + padding, .90 * height);
		    });

		    // Draw libs
		    p.stroke('#ef4923');
		    $(libraries).each(function(i, time_of_creation) {
		      // Draw a line for each user in our list
		      p.line(ratio * time_of_creation + padding, .05 * height, ratio * time_of_creation + padding, .90 * height);
		    });

		    draw_scaffolding();

		}

	});


}

function draw_scaffolding() {

	p.strokeWeight(1);
	p.stroke(150);
	p.line(padding, .93 * height + padding, padding, .93 * height - padding); // left tick
	p.line(width - 1, .93 * height + padding, width - 1, .93 * height - padding);  // right tick
	p.line(padding, .93 * height, width - 1, .93 * height); // long, base line

	p.line(ratio * last_minute_of_day, .93 * height + padding, ratio * last_minute_of_day, .93 * height - padding);  // clock tick
	
	$('.new_day').css('left', 6);
	$('.six_am').css('left', width * .25);
	$('.noon').css('left', width * .5);
	$('.six_pm').css('left', width * .75);
	$('.midnight').css('left', width * .95);

	$('.today .users').html(users.length + ' users');
	$('.today .orgs').html(orgs.length + ' organizations');
	$('.today .libraries').html(libraries.length + ' libraries');
	$('.today .archives').html(archives.length + ' archives');

}


};

new p5(today_vis);

