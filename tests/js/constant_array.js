var a = ["const", 2, notaconstant];
var b = a[0];
var c = a[1];
var d = a[2];

a[1] = notaconstant;
b = a[1];
