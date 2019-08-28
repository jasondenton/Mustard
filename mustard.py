from copy import copy, deepcopy
from functools import reduce
import json
from os import environ
import numpy as np 
from random import randrange, seed

GAME_SYSTEMS = {}

def group_by(lst, grouping=lambda x:x, sorting=lambda x:x, rev=False):
	'''Group a list into a list of sublists accordding to a grouping function.'''
	groups = []
	_lst = sorted(lst,key=sorting,reverse=rev)
	gval = grouping(_lst[0])
	nxtgp = [_lst[0]]
	for item in _lst[1:]:
		ngv = grouping(item)
		if not ngv or gval != ngv:
			groups.append(nxtgp)
			nxtgp = [item]
			gval = ngv
		else:
			nxtgp.append(item)
	groups.append(nxtgp)
	return groups

class GameSystem:
	def __init__(self, gsystem):
		if gsystem not in GAME_SYSTEMS:
			raise RuntimeError('Game system %s not defined.' % gsystem)
		definition = GAME_SYSTEMS[gsystem]
		self.name = definition['name']
		self.min_players = definition['min_players']
		self.max_players = definition['max_players']
		self.refname = definition['refname']
		self.roles = {}
		for r in definition['roles'].keys() :
			self.roles[r] = np.array(definition['roles'][r])
		self.num_roles = 0
		for k in self.roles.keys():
			if len(self.roles[k]) > self.num_roles:
				self.num_roles = len(self.roles[k])

def init_game_data(gpath):
	global GAME_SYSTEMS
	if not gpath: gpath = 'gamesystems.json'
	try:
		with open('gamesystems.json', 'r') as fin:
			gtmp = json.load(fin)
			GAME_SYSTEMS.update(gtmp)
	except:
		msg = 'Failed to load game system definitions from %s.' % gpath
		msg = msg + 'You can control where this file is loaded from by setting environmental variable GAMESYSTEMPATH.'
		raise RuntimeError(msg)
	seed()

class TableAssignment:
	def __init__(self):
		self.gm = None
		self.players = []
		self.seats = 0
		self.refname = "Game Master"
		self.start_time = None
		self.end_time = None
		self.pass_through = None
		self.id = None
		self.sub_id = None

	def as_dict(self):
		return {
			'gm' : self.gm.as_dict() if self.gm else None,
			'players' : [x.as_dict() for x in self.players],
			'start_time' : self.start_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
			'end_time' : self.end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
			'pass_through' : self.pass_through,
			'id' : self.id,
			'sub_id' : self.sub_id,
			'seats' : self.seats,
			'refname' : self.refname
		}

class WaitList:
	def __init__(self, w):
		self.players = w
		self.start_time = None
		self.end_time = None
		self.pass_through = None
		self.id = None

	def as_dict(self):
		return {
			'players' : [x.as_dict() for x in self.players],
			'start_time' : self.start_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
			'end_time' : self.end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
			'pass_through' : self.pass_through,
			'id' : self.id
		}

class Player:
    def __init__(self):
        self.name = None
        self.team = None
        self._roles = []
        self._level = 0
        self.id = None
        self._rolev = None

    def as_dict(self):
    	return {
    		'name' : self.name,
    		'team' : self.team,
    		'id' : self.id
    	}

    def add_role(self, role,lvl = 9):
    	self._roles.append((role,lvl))

class TableGroup:
	"""TableGroup objects are typically created and initalized by a front end driver,
	reading from some data source such as a warhorn import."""
	def __init__(self, gsystem):
		self.gmlist = []
		self.players = []
		self.tables = 0
		self.seats_per_table = 0
		self.event = None
		self.start_time = None
		self.end_time = None
		self.pass_through = {}
		self.id = None
		if gsystem: self._game_system = GameSystem(gsystem)
		else: self._game_system = GameSystem('Default')

	def _TableAssignment(self):
		ta = TableAssignment()
		ta.pass_through = deepcopy(self.pass_through)
		ta.seats = self.seats_per_table
		ta.refname = self._game_system.refname
		ta.start_time = self.start_time
		ta.end_time = self.end_time
		ta.event = self.event
		ta.id = self.id
		return ta 

	def _WaitList(self, wlist, sub_id):
		w = WaitList(wlist)
		w.event = self.event
		w.start_time = self.start_time
		w.end_time = self.end_time
		w.pass_through = deepcopy(self.pass_through)
		w.id = self.id
		w.sub_id = sub_id
		return w

	def message_log(self):
		msgs = []
		end_seating = False
		desc = self.event + ' on ' + self.start_time.strftime('%B %d at %I:%M%p ')

		if self.seats_per_table < self._game_system.min_players or self.seats_per_table > self._game_system.max_players:
			msgs.append((desc + 'does not seat a legal table for %s. It was assumed '
			'to be an administrative signup and was removed from the schedule.' 
			% self._game_system.name, 1))
			end_seating = True

		if not len(self.gmlist) and not len(self.players):
			msgs.append((desc + 'has no players and no %ss.' % self._game_system.refname,2))
		elif not len(self.gmlist):
			msgs.append((desc + 'has no %ss.' % self._game_system.refname,3))
		elif not len(self.players):
			msgs.append((desc + 'has no players signed up.',4))
		elif self.tables > len(self.gmlist):
			need = self.tables - len(self.gmlist)
			msgs.append((desc + 'needs %d more %ss.' % (need, self._game_system.refname),5))
		return (msgs,end_seating)

	def seat_players(self):
		"""This should be the only public function, producing an array of TableAssignments
		for the TableGroup"""
		(msgs, end) = self.message_log()
		if end: return [msgs]

		tables = []
		num_tables = min(self.tables, len(self.gmlist))
		extra_tables = max(self.tables - len(self.gmlist),0)
		max_seats = num_tables * self.seats_per_table
		plist = self.players[:max_seats]
		sub_id = 0
		for i in range(0,num_tables):
			ta = self._TableAssignment()
			sub_id += 1
			ta.sub_id = sub_id
			if i < len(self.gmlist):
				ta.gm = self.gmlist[i] 
			tables.append(ta)
		if num_tables:
			if len(plist) <= self.seats_per_table:
				tables[0].players = plist
			else:
				ts = TableSolver(self)
				seating = ts.seat_players()
				for i in range(0,len(seating)):
					tables[i].players = seating[i]
		npos = max_seats
		if extra_tables:
			for i in range(0, extra_tables):
				ta = self._TableAssignment()
				sub_id += 1
				ta.sub_id = sub_id
				ta.players = self.players[npos:npos+self.seats_per_table]
				tables.append(ta)
				npos += self.seats_per_table
		wlist = self.players[npos:]
		if wlist:
			sub_id += 1
			tables.append(self._WaitList(wlist,sub_id))

		tables.append(msgs)
		return tables

class TableSolver:
	'''Balance and seat large groups of players across large numbers of tables.
	No user serviceable parts.'''
	def __init__(self,tg):
		self.table_group = tg
		max_tables = min(tg.tables, len(tg.gmlist))
		max_seats = max_tables * tg.seats_per_table

		self.num_roles = self.table_group._game_system.num_roles
		self.target = np.ones(self.num_roles)
		self.to_seat = min(len(self.table_group.players), max_seats)
		self.seats_per_table = tg.seats_per_table
		self.need_tables = (self.to_seat // tg.seats_per_table)
		if self.to_seat % tg.seats_per_table: self.need_tables += 1
		self.need_tables = min(self.need_tables, max_tables)
		self.players = tg.players[:self.to_seat]
		self.setup_players()
		self.seating_groups()
		self.seating = [-1] * len(self.assignable)
		
	def player_lists_for_seating(self):
		'''Turn a seating chart in terms of assignable units to list sof players.'''
		tables = []
		for i in range(0,self.need_tables):
			tables.append([])
		for i in range(0,len(self.seating)):
			table_num = self.seating[i]
			grp = self.assignable[i]
			for p in grp:
				tables[table_num].append(p)
		return tables 

	def seat_players(self):
		self.initial_seating()
		self.fix_seating()
		return self.player_lists_for_seating()

	def num_tables_to_muster(num_gm, num_pc, num_locations):
		max_tables = max()

	def setup_players(self):
		'''Prepare player input objects for actual use.'''
		for p in self.players:
			if not p._roles: continue
			accum = np.zeros(self.num_roles)
			lvls = 0
			blocks = 0
			for r in p._roles:
				if not r[0]: continue
				if not r[1]: continue
				use_role = r[0].lower()
				if use_role not in self.table_group._game_system.roles: continue
				accum = accum + self.table_group._game_system.roles[use_role] * r[1]
				lvls += r[1]
				blocks = 1
			if lvls: accum = accum / lvls
			for r in p._roles:
				if not r[0]: continue
				if r[1]: continue
				use_role = r[0].lower()
				if use_role not in self.table_group._game_system.roles: continue
				accum = accum + self.table_group._game_system.roles[use_role] 
				blocks += 1
			if blocks: accum = accum / blocks
			p._rolev = accum
			p._level = 0
			for r in p._roles:
				if r[1]: p._level += r[1]

	def initial_seating(self):
		'''Initial seating without regard to table balance. Might be worth improving.'''
		units = len(self.seating)
		tidx = 0
		sitting = [0] * self.need_tables
		for i in range(0,units):
			while (sitting[tidx] + len(self.assignable[i])) > self.seats_per_table:
				tidx = (tidx + 1) % self.need_tables
			sitting[tidx] += len(self.assignable[i])
			self.seating[i] = tidx
			tidx = (tidx + 1) % self.need_tables
			
	def split_groups(self,roster):
		'''Split a large group into a seatable groups'''
		to_remove = []
		to_add = []
		for g in roster:
			if len(g) > self.seats_per_table:
				sp = int(len(g) / 2)
				g1 = g[0:sp]
				g2 = g[sp:]
				to_remove.append(g)
				to_add.append(g1)
				to_add.append(g2)
		for x in to_remove:
			roster.remove(x)
		roster = roster + to_add
		if to_add: return self.split_groups(roster)
		return roster
			
	def seating_groups(self):
		'''Term a list of players into a list of assignable units. Assignable
		units are teams or individual players.'''
		roster = group_by(self.players, 
			grouping=lambda x:x.team.lower() if x.team else None,
			sorting=lambda x:x.team.lower() if x.team else 'ZZZZZZZZ')
		self.assignable = self.split_groups(roster)
		self.assignable.sort(key=lambda x: len(x), reverse=True)

	def score_table(self, tbnum):
		'''Error functino for table balance. Lower scores are better.'''
		error = 0.0
		total_roles = np.zeros(self.num_roles)
		unknown_roles = 0
		known_roles = 0
		lvled = 0
		total_levels = 0
		seated = 0
		plist = []
		for i in range(0,len(self.seating)):
			if self.seating[i] != tbnum: continue
			pu = self.assignable[i]
			for p in pu:
				seated += 1
				plist.append(p)
				if np.sum(p._rolev):
					total_roles += p._rolev
					known_roles += 1
				else:
					unknown_roles += 1
				if p._level:
					total_levels += p._level
					lvled += 1
		erole = sum(np.maximum(0,self.target - total_roles) ** 2)
		erole -= (1 - (0.6 ** erole)) * unknown_roles
		error = max(0, erole) * 100
		if lvled: avg_lvl = total_levels / lvled
		dev = 0
		for p in plist:
			if not p._level: dev += 1
			else: dev += (avg_lvl - p._level) ** 2
		error += dev
		if seated > self.seats_per_table or seated < self.table_group._game_system.min_players:
			error += 100000.0
		return error

	def fix_seating(self):
		'''Keep swapping people until we can no longer reduce the error.
		Attempts to raise efficency or improve seating should start here.'''
		scores = []
		found = []
		for i in range(0, self.need_tables):
			scores.append(self.score_table(i))
		min_pos = self.need_tables
		max_pos = len(self.seating)
		max_fails = max_pos ** 2
		fails = 0
		while fails < max_fails:
			seat1 = randrange(min_pos,max_pos)
			table1 = self.seating[seat1]
			seat2 = randrange(min_pos,max_pos)
			table2 = self.seating[seat2]
			if table1 == table2:
				fails += 1 
				continue
			target = scores[table1] + scores[table2]

			self.seating[seat1] = table2
			self.seating[seat2] = table1
			s1 = self.score_table(table1)
			s2 = self.score_table(table2)
			if (s1 + s2) < target:
				scores[table1] = s1
				scores[table2] = s2
				fails = 0
			else:
				self.seating[seat1] = table1
				self.seating[seat2] = table2
				fails += 1

class LocationManager:
	'''Class to organize the machinery of assigning table numbers. Call book_tables instead.'''
	def __init__(self, tables):
		self.affinity_by_table = {}
		self.affinity_by_gm = {}
		self.in_use = []
		self.idle = []
		self.used = 0
		self.tables = tables 
		self.events = []
		for i in range(0,len(tables)):
			t = tables[i]
			self.events.append(('S', t.start_time, i))
			self.events.append(('E', t.end_time, i))
		self.events.sort(key=lambda x: str(x[1]) + x[0])

	def table_affinity(self,gm):
		tab_gm = None
		tab = self.affinity_by_gm.get(gm, None)
		if tab: tab_gm = self.affinity_by_table.get(tab, None)
		if tab_gm == gm: return tab
		return None

	def update_affinity(self,gm,tab):
		self.affinity_by_gm[gm] = tab 
		self.affinity_by_table[tab] = gm

	def assign_group(self,heat):
		rnd2 = []
		for h in heat:
			table = self.tables[h[2]]
			gm = table.gm 
			location = self.table_affinity(gm)
			if location and location in self.idle:
				self.idle.remove(location)
				self.in_use.append(location)
				table.location = location
			else:
				rnd2.append(h)
		for h in rnd2:
			table = self.tables[h[2]]
			if self.idle:
				to_rm = min(self.idle)
				location = to_rm
				self.idle.remove(to_rm)
			else:
				self.used += 1
				location = self.used
			self.in_use.append(location)
			table.location = location
			self.update_affinity(table.gm, table.location)

	def release_group(self,heat):
		for h in heat:
			location = self.tables[h[2]].location
			self.in_use.remove(location)
			self.idle.append(location)

	def set_locations(self):
		events = []
		for i in range(0,len(self.tables)):
			t = self.tables[i]
			events.append(('S', t.start_time, i))
			events.append(('E', t.end_time, i))
		gropued_events = group_by(events,
			grouping=lambda x:x[0],
			sorting=lambda x:str(x[1]) + x[0])
		for group in gropued_events:
			if group[0][0] == 'S':
				self.assign_group(group)
			else:
				self.release_group(group)

def daily_schedule(tables):
	time_slots = group_by(tables,
		grouping=lambda x:x.start_time,
		sorting=lambda x:x.start_time)
	for slot in time_slots:
		slot.sort(key=lambda x:x.event)
	daily = group_by(time_slots,
		grouping=lambda x:x[0].start_time.strftime('%Y%j') ,
		sorting=lambda x:1)
	return daily

def seat_table_groups(tgroups):
	if not isinstance(tgroups, list):
		tgroups = [tgroups]

	output = []	
	for g in tgroups:		
		output = output + g.seat_players()

	tables = list(filter(lambda x:isinstance(x, TableAssignment), output))
	waitlists = list(filter(lambda x:isinstance(x, WaitList), output))
	messages = reduce(lambda x,y: x+y, list(filter(lambda x:isinstance(x, list), output)))
	messages.sort(key=lambda x:x[1])
	messages = [x[0] for x in messages]
              
	lm = LocationManager(tables)
	lm.set_locations()

	schedule = daily_schedule(tables+waitlists)

	return {
		'tables' : tables,
		'waitlists' : waitlists,
		'messages' : messages,
		'schedule' : schedule,
		'locations_needed' : lm.used
	}





