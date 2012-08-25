$(document).ready(function(){
   
   render(time_matrix);
   
   var label = 'Days most active';
   
   var labels = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
   
   /*
    *
    * Following implementation for a pie chart on d3.js have been directly taken
    * from:
    * http://stackoverflow.com/questions/10502357/d3-js-pie-chart-labels-for-slices-not-tweening
    * http://jsfiddle.net/MX7JC/9/
    *
    * The snippet above has been modified a little to match the context here.
    *
    *
    */
   
   var w = 320,                       // width and height, natch
   	h = 320,
        r = Math.min(w, h) / 2,        // arc radius
        dur = 750,                     // duration, in milliseconds
        color = d3.scale.category10(),
        donut = d3.layout.pie().sort(null),
        arc = d3.svg.arc().innerRadius(r - 70).outerRadius(r - 20);
    
    var svg = d3.select("#dayGraph").append("svg:svg")
        .attr("width", w).attr("height", h);
    
    var arc_grp = svg.append("svg:g")
        .attr("class", "arcGrp")
        .attr("transform", "translate(" + (w / 2) + "," + (h / 2) + ")");
    
    var label_group = svg.append("svg:g")
        .attr("class", "lblGroup")
        .attr("transform", "translate(" + (w / 2) + "," + (h / 2) + ")");
    
    // GROUP FOR CENTER TEXT
    var center_group = svg.append("svg:g")
        .attr("class", "ctrGroup")
        .attr("transform", "translate(" + (w / 2) + "," + (h / 2) + ")");
    
    // CENTER LABEL
    var pieLabel = center_group.append("svg:text")
        .attr("dy", ".35em").attr("class", "chartLabel")
        .attr("text-anchor", "middle")
        .text(label);
    
    // DRAW ARC PATHS
    var arcs = arc_grp.selectAll("path")
        .data(donut(day_frequency));
    arcs.enter().append("svg:path")
        .attr("stroke", "white")
	.attr("title", function(d, i) { return (day_frequency[i].toFixed(2) * 100) + "%"; })
        .attr("stroke-width", 0.5)
        .attr("fill", function(d, i) {return color(i);})
        .attr("d", arc)
	.attr("class", "arc")
        .each(function(d) {this._current = d});
    
    // DRAW SLICE LABELS
    var sliceLabel = label_group.selectAll("text")
        .data(donut(day_frequency));
    sliceLabel.enter().append("svg:text")
        .attr("class", "arcLabel")
        .attr("transform", function(d) {return "translate(" + arc.centroid(d) + ")"; })
        .attr("text-anchor", "middle")
        .text(function(d, i) { var res = (day_frequency[i] == 0.0) ? "" : labels[i]; return res;  });
	
	
    $("#dayGraph .arc").tipsy({
	fade: true,
	gravity: $.fn.tipsy.autoNS
      });   
       
});