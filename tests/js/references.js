var a = ["const", 2, notaconstant];

var b = a;
c = b[1];
d = b[0];

b = a;
b[0] = 2;
console.log(a[0]); // Check `b` is still a reference to `a`
