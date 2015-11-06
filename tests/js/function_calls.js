var a = 1;
var b = a.toString(); // This should not be replaced
var c = a; // `a` is still a constant

var d = "foo";
var e = d.indexOf('f'); // This should be replaced
var f = d; // `d` is still a constant

var g = {"a": "foo"};
var h = g.a.indexOf('f');
var i = g.a; // Should still be a constant

var j = g.foo();
var k = g.a; // `g` is no longer a constant
