var a = {'b': 1};
var c = a.b;
var d = a['b'];

a.b = 2;
var e = a.b;

a.b = notaconstant;
var f = a.b;

// Make sure other values haven't changed
var g = c;
