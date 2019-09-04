Requires python 3.7 or later.

This package contains the program automuster.py, a simple command lien tool that parses data exported from Warhorn.net, musters it into a set of table assignments, and then stamps that data into a template for physical sign up sheets. This is useful if the 'workflow' for your convention involves pre-registration for events and sign up sheets hanging on the wall.

To use, you must have python3 installed. If python3 is not installed at /usr/local/bin, then change the first line of automuster.py to point to the appropriate location.

Usage:
`./automuster.py <<exported data, json format>>

Note that the exported data should be for the whole event. This is the data that is composed of a top level dictionary with a single field, slots, which is then an array of slots.

Output will be written to one or more files named "Signed up for <<venue>>.html", where venue is the name of the venue in the warhorn data. Output can be customized by changing the contents of signup.template.html, which is a jinj2 template.