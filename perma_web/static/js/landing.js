$(function(){
    /*** Perma In Action stuff ***/
    var $example=$('#example'),
        $examples=$('#examples'),
        exampleData={

            // all numbers represent PERCENTAGE of the image width/height

            MSC_1:{
                url:'http://courts.mi.gov/Courts/MichiganSupremeCourt/Clerks/Recent%20Opinions/13-14-Term-Opinions/147261-Opinion.pdf',
                cite:'<i>People v. Bynum</i>, Docket No. 147261, 2014 WL 3397199, --- N.W.2d --- (2014)',
                defaultLinkHeight:2,
                defaultLinkWidth:25,
                links:[{
                    url:'http://perma.cc/P8WZ-Y88E',
                    bbox:{left:61,top:78}
                },{
                    url:'http://perma.cc/XC2R-2M36',
                    bbox:{left:12,top:91}
                }]
            },
            MSC_2:{
                url:'http://courts.mi.gov/Courts/MichiganSupremeCourt/Clerks/Recent%20Opinions/13-14-Term-Opinions/146791-3-Opinion.pdf',
                cite:'<i>State ex rel. Gurganus v. CVS Caremark Corp.</i>, Docket No. 146792, 2014 WL 2616577, --- N.W.2d --- (2014)',
                defaultLinkHeight:2,
                defaultLinkWidth:27,
                links:[{
                    url:'http://perma.cc/V5MG-DHLF',
                    bbox:{left:24,top:75}
                }]
            },
            MSC_3:{
                url:'http://courts.mi.gov/Courts/MichiganSupremeCourt/Clerks/Recent%20Opinions/13-14-Term-Opinions/146033-Opinion.pdf',
                cite:'<i>In re Forfeiture of Bail Bond</i>, Docket No. 146033, 2014 WL 2892394, --- N.W.2d --- (2014)',
                defaultLinkHeight:2,
                defaultLinkWidth:25,
                links:[{
                    url:'http://perma.cc/Z992-2ZMQ',
                    bbox:{left:25,top:86}
                }]
            },

            HLR_1:{
                url:'http://cdn.harvardlawreview.org/wp-content/uploads/2014/05/vol127_Kwak.pdf',
                cite:'James Kwak, <i>Incentives and Ideology</i>, 127 Harv. L. Rev. F. 253 (2014)',
                defaultLinkHeight:2,
                defaultLinkWidth:23,
                links:[{
                    url:'http://perma.cc/X5LP-7TRT',
                    bbox:{left:39,top:62}
                },{
                    url:'http://perma.cc/84DZ-9XCE',
                    bbox:{left:61,top:66}
                },{
                    url:'http://perma.cc/JP7X-DWVZ',
                    bbox:{left:20,top:72}
                }]
            },
            HLR_2:{
                url:'http://cdn.harvardlawreview.org/wp-content/uploads/2014/06/vol127_west.pdf',
                cite:'Sonja R. West, <i>Press Exceptionalism</i>, 127 Harv. L. Rev. 2434 (2014)',
                defaultLinkHeight:2,
                defaultLinkWidth:23,
                links:[{
                    url:'http://perma.cc/W56K-RQRD',
                    bbox:{left:13,top:39}
                },{
                    url:'http://perma.cc/ML5Q-E4LG',
                    bbox:{left:55,top:45}
                },{
                    url:'http://perma.cc/W32Z-BFXK',
                    bbox:{left:75,top:51,right:87}
                },{
                        url:'http://perma.cc/W32Z-BFXK',
                        bbox:{left:10,top:53,right:23}
                },{
                    url:'http://perma.cc/D5CD-UQ4T',
                    bbox:{left:70,top:57,right:88}
                },{
                        url:'http://perma.cc/D5CD-UQ4T',
                        bbox:{left:10,top:59,right:17}
                },{
                    url:'http://perma.cc/48VC-ZS62',
                    bbox:{left:12,top:66}
                },{
                    url:'http://perma.cc/5N7Z-QDKB',
                    bbox:{left:59,top:74}
                },{
                    url:'http://perma.cc/4983-ZCHN',
                    bbox:{left:54,top:82}
                }]
            },
            HLR_3:{
                url:'http://cdn.harvardlawreview.org/wp-content/uploads/2014/06/vol127_Symposium_Zittrain.pdf',
                cite:'Jonathan Zittrain, <i>Engineering an Election</i>, 127 Harv. L. Rev. F. 335 (2014)',
                defaultLinkHeight:2.4,
                defaultLinkWidth:23,
                links:[{
                    url:'http://perma.cc/W855-VYSW',
                    bbox:{left:57,top:67}
                },{
                    url:'http://perma.cc/6YVS-8QWH',
                    bbox:{left:38,top:76}
                }]
            }

        };
    $examples.find('a.btn').on('click', function(){
        var $this=$(this);
        if(!$this.hasClass('selected')){
            var key = $this.attr('data-img'),
                data = exampleData[key];

            // mark clicked button as selected, deselect others
            $examples.find('a.btn').removeClass('selected');
            $this.addClass('selected');

            // get set up for animation that will be triggered when image loads
            $examples.height($examples.height());
            $example.show();

            // fill in content
            var imgURL = settings.STATIC_URL+'img/examples/'+key+(isHighDensity()?'@2x':'')+'.gif';
            $example.find('img').attr('src', imgURL);
            $example.find('#example-title > span').html("<a href='"+data.url+"'>"+data.cite+"</a>");
            $example.find('#example-image-wrapper .example-link').remove();
            for(var i=0, len=data.links.length; i<len; i++){
                var link = data.links[i],
                    bbox = link.bbox,
                    width = bbox.right ? bbox.right-bbox.left : data.defaultLinkWidth,
                    height = bbox.bottom ? bbox.bottom-bbox.top : data.defaultLinkHeight;
                $example.find('#example-image-wrapper').append("<a class='example-link' href='"+link.url+"' style='"+
                                                                   "left:"+bbox.left+"%;"+
                                                                   "top:"+bbox.top+"%;"+
                                                                   "width:"+width+"%;"+
                                                                   "height:"+height+"%;"+
                                                               "'> </a>");
            }

            // make sure content is in view
            $('html, body').animate({
                scrollTop: $example.offset().top-10
            }, 1000);

        }else{
            // they clicked the same button again; hide the $example panel
            $this.removeClass('selected');
            $examples.animate({
                height: $example.offset().top - $examples.offset().top
            }, 500, function(){
                $example.hide();
                $examples.css("height", ""); // once height animation is done, go back to auto height
            });
        }
        return false;
    });
    $example.find('img').on('load', function(){
        $examples.animate({
            height: $example.offset().top + $example.height() - $examples.offset().top
        }, 500, function(){
            $examples.css("height", ""); // once height animation is done, go back to auto height
        });
    });


    /*** map drawing stuff ***/

    var paper = new ScaleRaphael('plot-map-container', 950, 590),
        map = paper.USMap();

    // handle resizing
    function resizePaper(){
        var newWidth = $("#plot-map-container").parent().width();
        paper.scaleAll(newWidth/map.width);
    }
    $(window).resize(resizePaper());
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
        [41.657435, -91.542964, "University of Iowa School of Law"]
    ];
    for(var i = 0; i < points.length; i++){
        //map.plot(points[i][0], points[i][1], points[i][2]);
        map.plot(points[i][0], points[i][1]);
    }

});
