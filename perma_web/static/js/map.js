$(function(){
    /*** map drawing stuff ***/

    var paper = new ScaleRaphael('plot-map-container', 950, 590),
        map = paper.USMap();

    // handle resizing
    function resizePaper(){
        var newWidth = $("#plot-map-container").parent().width();
        paper.scaleAll(newWidth/map.width);
    }
    $(window).resize(resizePaper);
    resizePaper();

    // plot points
    var points = [
        [38.944794, -77.095004, "Pence Law Library, Washington College of Law, American University"],
        [42.341822, -71.195736, "Law Library at Boston College, Boston College of Law"],
        [38.944794, -77.095004, "Pence Law Library, Washington College of Law, American University"],
        [42.350527, -71.109665, "Pappas Law Library, Boston University School of Law"],
        [39.953772, -75.193314, "Biddle Law Library, University of Pennsylvania Law School"],
        [32.790682, -79.938873, "Charleston School of Law Library"],
        [40.000906, -105.262076, "William A. Wise Law Library, Colorado Law"],
        [40.806948, -73.960331, "Arthur W. Diamond Law Library, Columbia Law School"],
        [42.443868, -76.485849, "Cornell University Law School"],
        [42.349480, -71.077708, "Digital Public Library of America"],
        [35.999711, -78.944995, "J. Michael Goodson Law Library, Duke University School of Law"],
        [30.439591, -84.286414, "Florida State Law Research Center, Florida State University College of Law"],
        [29.650052, -82.359510, "University of Florida Levin College of Law"],
        [40.771128, -73.984648, "The Leo T. Kissam Memorial Library, Fordham University School of Law"],
        [38.898086, -77.012985, "Georgetown Law Library, Georgetown Law"],
        [42.379400, -71.119587, "Harvard Law School Library"],
        [39.772174, -86.167720, "Ruth Lilly Law Library, Robert H. McKinney School of Law, Indiana University"],
        [41.877710, -87.628618, "Louis L. Biro Law Library, The John Marshall Law School"],
        [41.699725, -86.238208, "Kresge Law Library, University of Notre Dame The Law School"],
        [34.066263, -117.647682, "College of Law Library, University of La Verne"],
        [45.452229, -122.677615, "Paul L. Boley Law Library, Lewis & Clark Law School"],
        [30.414529, -91.175239, "Louisiana State University Law Library, LSU Law Center"],
        [41.897352, -87.627156, "Loyola University Chicago School of Law"],
        [39.289763, -76.622936, "Thurgood Marshall Law Library, Francis King Carey School of Law, University of Maryland"],
        [-37.802327, 144.960055, "Melbourne Law School Library, The University of Melbourne"],
        [40.818056, -96.699848, "University of Nebraska College of Law"],
        [41.896683, -87.619690, "Pritzker Legal Research Center, Northwestern Law"],
        [39.996168, -83.008418, "Michael E. Moritz Law Library, Ohio State University"],
        [51.757111, -1.247840, "Bodleian Law Library, Bodleian Libraries, University of Oxford"],
        [34.037931, -118.707359, "Harnish Law Library, Pepperdine University School of Law"],
        [37.574272, -77.541348, "William Taylor Muse Law Library, University of Richmond School of Law"],
        [29.752922, -95.365044, "The Fred Parks Law Library, South Texas College of Law"],
        [37.423975, -122.167550, "Robert Crown Law Library, Stanford Law School"],
        [34.072966, -118.438463, "Hugh & Hazel Darling Law Library, UCLA School of Law"],
        [25.720798, -80.279734, "University of Miami School of Law"],
        [34.363963, -89.541439, "Grisham Law Library, University of Mississippi School of Law"],
        [36.107131, -115.142426, "Wiener-Rogers Law Library, UNLV William S. Boyd School of Law"],
        [32.771408, -117.188822, "Pardee Legal Research Center, University of San Diego"],
        [30.289088, -97.731251, "Tarlton Law Library, Jamail Center of Legal Research, The University of Texas School of Law"],
        [40.762004, -111.851903, "S.J. Quinney Law Library, University of Utah"],
        [36.145869, -86.799537, "Vanderbilt Law School"],
        [38.051897, -78.510371, "Arthur J. Morris Law Library, University of Virginia School of Law"],
        [47.655295, -122.303745, "University of Washington School of Law"],
        [38.649789, -90.312022, "Washington University Law"],
        [37.264720, -76.705315, "William & Mary Law School"],
        [43.074277, -89.401986, "University of Wisconsin Law Library"],
        [41.311960, -72.927899, "Lillian Goldman Law Library, Yale Law School"],
        [40.736568, -74.1665841, "Peter W. Rodino, Jr. Law Library, Seton Hall Law"],
        [35.904912, -79.046913, "Kathrine R. Everett Law Library, University of North Carolina"],
        [39.817224, -75.546148, "Widener University School of Law"],
        [32.846348, -96.786086, "SMU Dedman School of Law"],
        [33.578997, -101.886574, "Texas Tech University School of Law"],
        [41.657435, -91.542964, "University of Iowa School of Law"],
        [43.036906, -87.926988, "Ray & Kay Eckstein Law Library, Marquette University"],
        [41.040253, -73.764685, "Pace Law School, Pace University"],
        [33.646735, -117.835965, "University of California, Irvine School of Law"]
    ];
    for(var i = 0; i < points.length; i++){
        //map.plot(points[i][0], points[i][1], points[i][2]);
        map.plot(points[i][0], points[i][1]);
    }

});
