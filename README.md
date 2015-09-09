# xnovacmd
Desktop client for [XNova](http://xnova.su/) browser game, written using Python 3 + Qt 5 (PyQt5)

Still a lot of work in progress, but I can see a light at the end.

Requirements to run:

 * Qt 5
 * Python 3
 * python modules: [requests](http://docs.python-requests.org/en/latest/), [PyExecJS](https://pypi.python.org/pypi/PyExecJS)
 * [PyQt5](http://pyqt.sourceforge.net/Docs/PyQt5/installation.html) and all its dependencies ([SIP](https://riverbankcomputing.com/software/sip/download), etc)

PyExecJS also requires a JS runtime be available in your system at runtime:
In Windows, built-in Microsoft Windows Script Host (JScript) is fine,
on Linux you'll probably need something like [Node.js](http://nodejs.org)