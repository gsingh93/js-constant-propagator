JavaScript Constant Propagator
==============================

Applies constant propagation and folding to JavaScript code.

Background
----------

Recently I've come across multiple pieces of JavaScript malware which looked something like this:

```javascript
var xdjs = ["\x6C\x65\x6E\x67\x74\x68", "\x62\x61\x73\x65\x36\x34\x44\x65\x63\x6F\x64\x65"];
var hkjk = xdjs[0];
var cfga = [0, 1, 2][hkjk];
...
```

It's clear that this code could be cleaned up a lot with some constant propagation. I'd expect that there would be already be some software to clean this up, but I wasn't able to find anything. With this project, this code simplifies to:

```javascript
var xdjs = ['length', 'base64decode'];
var hkjk = 'length';
var cfga = [0, 1, 2]['length'];
...
```

Note that this project doesn't yet perform dead code elimination, but when it does this will simplify to:

```javascript
var cfga = [0, 1, 2]['length'];
```

Further improvements would be to implement constant function and property elimination, but those also have not been implemented and are currently not on the roadmap (but PRs are welcome).

Installation and Usage
----------------------

Install `slimit` using `pip`:

```
pip install slimit
```

Clone the repository or download the script and then run:

```
./constant-propagator.py infile.js
```

The minimized JavaScript will be output to stdout.
