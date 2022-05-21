# Table Mustering with Mustard

Mustard is a python package to support the scheduling of people signed up to play RPG games at conventions and other large public events. It turns a list of players signed up for an event consisting of multiple tables of play into a seating arrangement for those playes (in RPG lingo, it musters tables for play).

## Use Mustard When:
1. You have electronic sign up data for your players.
2. You need to keep teams or families together when tables are mustered.
3. You want to balance the classes/roles at each table even if the available data is incomplete.
4. You want to game masters from having to move when running consecutive slots.
5. You need to ensure seating priority is maintained.

This repository contains the core mustard python module, and a module to parse data exported from Warhorn.net, which doubles as an example of how to write the factory methods which feed data to mustard. The file automuster.py is a command line tool, which turns exported Warhorn data into HTML format, printable signup sheets suitable for posting on the wall at a convention.

## Understand and Using Mustard

Making use of mustard involves calling init\_game\_data() to initialize the system and load a library of game system data, creating and populating one or more TableGroup objects, then calling seat_table_groups() to muster those tables. The return value of seat_table_groups is a dictionary providing the seating arrangements and other data such as wait lists.

Most of the work of using Mustard is in creating TableGroup objects, which in turn need to be populated with Player objects. In most cases, this will mean writing factory methods for these two objects, which create empty instances and then populate them from a data source. The provided file, warhorn.py, provides a working example of how to do this for data exported from Warhorn.net sign ups.

## Mustard Objects, Methods, and Functions

Mustard is organized around two functions, two input objects, and two output objects. The Player and TableGroup objects are used to represent players and tables to be mustered, and the TableAssignment and WaitList objects represent the results of the mustering operation. The two functions initialized the system, and then produce the output objects from the input objects.

### init\_game\_data(file_path)

The `init\_game\_data()` function loads a library of game data for mustard to use when attempting to balance classes and roles at a table. It needs to be called before the first table group is created. `init\_game\_data` takes one parameter, a string containing the path to load the data from. If no value is provided, it will attempt to load the data from the file 'gamesystems.json' in the current working directory. Multiple calls to `init\_game\_data` can be made to load data from multiple files.

### Player

`Player` objects represent players and game masters to the Mustard system. The constructor for the class creates an object with empty name, id, and team fields, but only the team field is used by mustard. The other fields are convenience fields, so calling software can distinguish different players. Additional fields added to Player objects will be retained when those objects are returned from mustering, attached to TableAssignment and WaitList objects. Such fields should not start with an underscore, least they conflict with internal book keeping.

The `add_role` method may be used to add classes or roles to a Player object. Each call may add one role and a corresponding level to the Player. Either one may be omitted, although role balancing works better with more information. If the role name is not understood, it is treated as unknown. Role names are understood based on the game system declared when creating a TableGroup, see below for details. For point based systems, use a character point value scaled to a range of 1 to 100 for the level. This method may be called more than once to add multiple classes or roles to a player.

The `as_dict` method can be called to retrieve a dictionary representing the Player object. This can be useful when there is a need to print object for debugging, or as the first step in returning the results of mustering in JSON format.


 Example:
```python
 import mustard

 p = mustard.Player()
 p.name = "John Doe"
 p.id = 1001
 p.team = "The Best Team"
 p.add_role('fighter' 3)
 p.add_role('wizard', 2)
```

### TableGroup

A TableGroup represents a collection of tables, game masters, and players to be scheduled together. 

The constructor for TableGroup takes a single argument, a string representing the name of the game system represented by the TableGroup. Legal values for this string are the keys of the dictionary found in the game settings file(s) loaded by the call(s) to init\_game\_data. Once this constructor is called to create a new TableGroup, the TableGroup must be fully instantiated before use, by directly setting a number of fields, as shown on the table below.

| Field | Usage |
| ---- | ---- |
| gmlist | A list of Player objects, representing those who will run the game. |
| players | A list of Player objects, representing those playing. Should be sorted by seating priority. |
| tables | The number of tables available to run this particular event or adventure. |
| seats_per_table | An integer, giving the maximum number of players to seat at each table. |
| event | A string, representing the name of the event. |
| start_time | A datetime object, representing the start time for the event. |
| end_time | A datetime object, representing the ending time for the event. |
| id | An arbitrary ID field, its value will be copied to the id field of every TableAssignment and WaitList created from this TableGroup. Optional. |
| pass_through | An initially empty dictionary. Every TableAssignment and WaitList created from this TableGroup will get a deepcopy of this dictionary. Optional. |

The ordering of the players field is important; it is assumed to be sorted by seating priority. Usually, this will be based on a first come, first serve sign up time stamp. But, mustard itself does not determine priority. It depends on the order of the list it is provided.

The field `pass_through`is initialized to an empty dictionary by the constructor. A TableGroup will ultimately produce one or more TableAssignments and WaitLists, and each will get a copy of the contents of this dictionary. Use this mechanism to attach additional useful information to each of those objects. For example, to attach a description of the scenario to be run.

#### seat\_table\_groups(tgroups)

The `seat\_table\_groups`takes either a single TableGroup, or a list of TableGroups, and musters those groups into a set of seated TableAssignments, and if necessary, WaitLists. Each TableGroup may potentially be for a different game system. It returns a dictionary with the following fields:

| Field | Usage |
| ---- | ---- |
| 'tables' | A list of TableAssignments representing all mustered tables.|
| 'waitlists' | A list of all WaitLists required to account for all players. Might be an empty list of no one ended up on a waitlist.|
| 'messages' | A list of messages produced during the mustering process. These are sorted by subject, and report conditions such as needed game masters and tables with no players.|
| 'schedule' | The tables and waitlists for the TableGroups, arranged in list based tree structure. See below.|
| 'locations_needed' | The number of locations needed to hold the event. Usually, this means physically tables to seat people at. Corresponds to the maximum value of found in a location field of the tables list. |

 The `schedule` field is meant to provide an organized way to iterate through the days and start times of a large event. It can be useful for producing event summaries or similar reports. Logically, `schedule` is a four level tree, represented by nested lists. The list in the schedule field is the root element. The elements of that root list represent days of the event. The elements of each day list represent distinct starting times for events. The next level of lists down contains TableAssignments and WaitLists that share a start_time value. Small events will likely prefer to use the `tables` and `waitlist` fields.

#### Table Mustering Algorithm

Mustering tables involves balancing a number of considerations, while observing constraints on seating and wait listing. Mustard musters tables from a TableGroup according to the following rules :

A confirmed table is one for which there is an available game master on the list provided with the TableGroup.

An unconfirmed table is one which the event has declared as available, but does not have a game master for. This occurs when the table group has declared more tables than games masters. (tables > len(gms)).

The maximum number of players, as determined by seats_per_table, will be seated at confirmed tables. These tables will be subject to the table balancing algorithm described below.

One confirmed tables are full, remaining players will be placed at unconfirmed tables until those tables are full, in the order they appear on the player list. Because seats at unconfirmed tables are not guaranteed play space, team grouping is not observed when placing these players. Consequently, some team members might get separated depending on where they appear on the prioritized list of players. Role and level balance is also not attempted for unconfirmed tables.

Any remaining players will be placed on the wait list.

If there are more confirmed seats than players, players will be spread across tables to minimize table size.

When attempting to muster confirmed tables, Mustard first guarantees that all team members who are seated at confirmed tables will stay together if possible. It will split a team up only if it is too large to seat every member at the same table.  When determining party balance, Mustard first considers party composition first. To break ties, it attempts to keep the difference in party levels to a minimum. Computations of party balance are based on game system data, see that section for an explanation.

These considerations should result in tables mustered according to what most convention organizers and attendees expect. That is, every ones seating priority is respected and teams are kept together when possible.

### TableAssignment

TableAssignment objects are returned as part of the data coming back from the call to `seat_table_groups`, and represent an assignment of players and game master to a single physical gaming table. There will be one TableAssignment produced for each table declared in the TableGroup. Most of the fields of a TableAssignment are copied down from the TableGroup that produced it.

| Field | Usage |
| ---- | ---- |
| gm | A player object representing the game master for this table. If set to None, this TableAssignment represents an unconfirmed table.|
| players | A list of player objects representing those player. Original seating priority not preserved is the gm field is set to something other than None.|
| seats | Maximum number of seats at this table. May or may not match len(players).|
| refname | What the referee or game master is called for this table, based on the game system declared by the table group.|
| start_time | The start time for this table, as determined by TableGroup.|
| end_time | The end time for this table, as determined by TableGroup.|
| id | The id of the TableGroup that produced this TableAssignment.|
| sub_id | Each TableAssignment produced from a particular TableGroup gets its own sub_id, starting at 1.|
| pass_through | A copy of the TableGroups pass_through dictionary.|

The `as_dict` method can be called to retrieve a dictionary representing the TableAssignment object. This can be useful when there is a need to print object for debugging, or as the first step in returning the results of mustering in JSON format.

### WaitList
Each TableGroup might produce one WaitList, if it can not seat all players at confirmed or unconfirmed tables.

| Field | Usage |
| ---- | ---- |
|players | A list of player objects representing those player. Original seating priority is preserved for WaitLists.|
| start_time | A datetime with the start time for this table, as determined by TableGroup.|
| end_time | A datetime with the end time for this table, as determined by TableGroup.|
| id | The id of the TableGroup that produced this TableAssignment.|
| pass_through | A copy of the TableGroups pass_through dictionary.|

The `as_dict` method can be called to retrieve a dictionary representing the TableAssignment object. This can be useful when there is a need to print object for debugging, or as the first step in returning the results of mustering in JSON format.

## Game System Data

The best way to understand the game system data that Mustard uses to balance roles at tables is to examine the sample data in the provided 'gamesystems.json' file. This file must be formatted in JSON, as a single dictionary object. The keys to this dictionary should be full names and editions of game systems; these are the values that are used to construct new TableGroup objects.

Each top level key in turn specifies another dictionary, with the following fields.

| Ket | Contains |
| ----- | ------ |
| name| The display name of the game system. |
| refname | Game Master, Dungeon Master, or whatever the system calls the referee. |
| min_players | Minimum players to muster for a table. |
| max_players | Maximum players to muster for a table. |
| roles | See below. |

The roles dictionary should be a mapping between the names of different classes or roles in the game system, and an array of floating point values of arbitrary length but consistent length. It is useful to think of this data as a table. Each row of the table corresponds to one class in the game system, and each column of the table represents a different role in the game. Each entry in the table reprsents how well a particular class fulfills are particular role. It it not important which role corresponds to which column, other than that the interpretation of which column represents which role is consistent across the rows. Each numberical value in the table should be a value from 0 to 1.0. The sum of all roles for a particular class need not be 1.0, some classes are better than others and do multiple things well. Players with multi-classes characters get a proportioned value of their classes, weighted by the relative portion of their levels in each class. A table is considered to be fully balanced for all roles when the sum of all player role values is 1.0 or greater for all roles (columns).

Note: All fields must be present in a definition, but only refname and roles are currently used by the system.

## A mostly complete example 
```python
from mustard import seat_table_groups, init_game_data

init_game_data()
...
players = []
for pdata = my_player_data
	player = Player()
	...
	player.add_role(clss, lvl)
	players.append(player)
	data = seat_table_groups(tgroups)
...
table_group = TableGroup('Dungeons & Dragons 5th Edition')
table_group.gm = players[0]
table_group.players = players[1:]
table_group.seats_per_table = 6
table_group.tables = 1
table_group.event = 'Plots in Motion'
table_group.start_time = datetime.datetime.now()
table_group.end_time = datetime.datetime.now() + datetime.timedelta(hours=6)
data = seat_table_groups(tgroups)
my_game = data['tables'][0]
waitlist = data['waitlists'][0]
```
