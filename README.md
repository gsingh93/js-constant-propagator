JavaScript Constant Propagator
==============================

Applies constant propagation and folding to JavaScript code. Note that while this project works for many small snippets of code, it is still early in development. Please see the Future Work section for what is not supported.

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

This could be further shortened to `var cfga = 3`, but this also has not been implemented.

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

Future Work
-----------

These are some improvements I'd like to add to this project, but don't have the time to do right now. Pull requests are welcome.

- Implement dead code elimination
- Support scopes
- Apply some simple functions to constants during constant folding, like `length` and any base64 functions
- Fix buggy handling of binary operators during constant folding (the current binary operators act as if the arguments are python numbers, not JavaScript numbers)
- Optionally rename arguments and variables to `arg1, arg2, ...` and `var1, var2, ...`
- Add support for constant functions
- Add support for constant object properties
- Convert `obj['property']` and `obj['function']()` to `obj.property` and `obj.function()`
- Add tests
