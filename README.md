# Table Mustering with Mustard

Mustard is a python package to support the scheduling of people signed up to play RPG games at conventions and other large public events. It turns a list of players signed up for an event consisting of multiple tables of play into a seating arrangement for those playes (in RPG lingo, it musters tables for play).

## Use Mustard When:
1. You have electronic sign up data for your players.
2. You need to keep teams or familys together when tables are mustered.
3. You want to balance the classes/roles at each table even if the available data is incomplete.
4. You want to game masters from having to move when running consecutive slots.
5. You need to ensure seating priority is maintained.

This repository contains the core mustard python module, and a module to parse data exported from Warhorn.net, which doubles as an example of how to write the factory methods which feed data to mustard. The file automuster.py is a command line tool, which turns exported Warhorn data into HTML format, printable signup sheets suitable for posting on the wall at a convention.

The file REFERENCE.md contains complete documentation of the mustard.py module and API, which can be use by other software to provide mustering functionality. The file USAGE.md described the included program automuster.py, which can be used to produce physical sign up sheets from data exported from Warhorn.

The files mustard.wsgi and application.py present a very simple web application which takes in POSTed JSON data is warhorn format, and returns the mustered table results as JSON.