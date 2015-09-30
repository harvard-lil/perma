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
            $example.find('img').attr('src','')         // remove URL so image load event will fire even if they click the same button twice
                                .attr('src', imgURL);   // then insert new URL
            $example.find('#example-title').html(data.cite+" <a class='outside' href='"+data.url+"'>View Original</a>");
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
            //$('html, body').animate({
            //    scrollTop: $example.offset().top-10
            //}, 1000);

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
});
    