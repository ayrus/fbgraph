/*
 *
 * Punchcard on d3.js by Jey Balachandran.
 *
 * Source: https://github.com/jeyb/d3.punchcard
 *
 * More: http://jeybalachandran.com/posts/San-Francisco-Caltrain-Punchcard/ 
 *
 *
 */

var pane_left = 120
  , pane_right = 800
  , width = pane_left + pane_right
  , height = 520
  , margin = 10
  , i
  , j
  , tx
  , ty
  , max;

// X-Axis.
var x = d3.scale.linear().domain([0, 23]).
  range([pane_left + margin, pane_right - 2 * margin]);

// Y-Axis.
var y = d3.scale.linear().domain([0, 6]).
  range([2 * margin, height - 10 * margin]);

// The main SVG element.
var punchcard = d3.
  select("#graph").
  append("svg").
  attr("width", width - 2 * margin).
  attr("height", height - 2 * margin).
  append("g");

// Hour line markers by day.
for (i in y.ticks(7)) {
  punchcard.
    append("g").
    selectAll("line").
    data([0]).
    enter().
    append("line").
    attr("x1", margin).
    attr("x2", width - 3 * margin).
    attr("y1", height - 3 * margin - y(i)).
    attr("y2", height - 3 * margin - y(i)).
    style("stroke-width", 1).
    style("stroke", "#99173C");

  punchcard.
    append("g").
    selectAll(".rule").
    data([0]).
    enter().
    append("text").
    attr("x", margin).
    attr("y", height - 3 * margin - y(i) - 5).
    attr("text-anchor", "left").
    text(["Sunday", "Saturday", "Friday", "Thursday", "Wednesday", "Tuesday", "Monday"][i]);

  punchcard.
    append("g").
    selectAll("line").
    data(x.ticks(24)).
    enter().
    append("line").
    attr("x1", function(d) { return pane_left - 2 * margin + x(d); }).
    attr("x2", function(d) { return pane_left - 2 * margin + x(d); }).
    attr("y1", height - 4 * margin - y(i)).
    attr("y2", height - 3 * margin - y(i)).
    style("stroke-width", 1).
    style("stroke", "#033649");
}

// Hour text markers.
punchcard.
  selectAll(".rule").
  data(x.ticks(24)).
  enter().
  append("text").
  attr("class", "rule").
  attr("x", function(d) { return pane_left - 2 * margin + x(d); }).
  attr("y", height - 3 * margin).
  attr("text-anchor", "middle").
  text(function(d) {
    if (d === 0) {
      return "12a";
    } else if (d > 0 && d < 12) {
      return d;
    } else if (d === 12) {
      return "12p";
    } else if (d > 12 && d < 25) {
      return d - 12;
    }
  });

function render(data) {
  // Data has array where indicy 0 is Monday and 6 is Sunday, however we draw
  // from the bottom up.
  data = data.slice(0).reverse();

  // Find the max value to normalize the size of the circles.
  max = 0;
  for (i = 0; i < data.length; i++) {
    max = Math.max(max, Math.max.apply(null, data[i]));
  }

  punchcard.
    selectAll("circle").
    transition().
    duration(750).
    attr("r", 0);

  punchcard.
    selectAll("circle").
    transition().
    delay(750).
    remove();

  // Show the circles on the punchcard.
  for (i = 0; i < data.length; i++) {
    for (j = 0; j < data[i].length; j++) {
      punchcard.
        data([data[i][j]]).
        append("circle").
        style("fill", "#73626E").
        attr("class", "circle").
        attr("title", function(d) { return d + " posts from you."; }).
        attr("r", function(d) { return d / max * 14; }).
        attr("transform", function() {
            tx = pane_left - 2 * margin + x(j);
            ty = height - 7 * margin - y(i);
            return "translate(" + tx + ", " + ty + ")";
          });
    }
  }

$("#graph .circle").tipsy({
    fade: true,
    gravity: "s"
  });
}