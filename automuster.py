#!/usr/bin/python3

import json
import sys
from pprint import PrettyPrinter
from warhorn import warhorn2mustard
from mustard import seat_table_groups, init_game_data
from jinja2_helper import HTMLTemplateEngine

def description_for_table(table):
	return {
		'event' : table.event,
		'min_level' : table.pass_through['min_level'],
		'max_level' : table.pass_through['max_level']
	}

def list_of_table_descriptions(tables):
	seen = {}
	unique_tables = []
	for t in tables:
		if t.event in seen: continue
		seen[t.event] = True
		unique_tables.append(description_for_table(t))
	unique_tables.sort(key = lambda x:x['event'])
	return unique_tables

class AutoMusterTemplateEngine(HTMLTemplateEngine):
	def __init__(self):
		HTMLTemplateEngine.__init__(self)
		self.template_env.filters['table_descs'] = list_of_table_descriptions

def main():
	init_game_data('gamesystems.json')
	fin_name = sys.argv[1]
	pp = PrettyPrinter()
	output = AutoMusterTemplateEngine()

	with open(fin_name, 'r', encoding='utf8') as fin:
		top = json.load(fin)
	slots = top['slots']
	slots_by_venue = {}
	for slot in slots:
		venue = slot['venue']
		vlist = slots_by_venue.get(venue,list())
		vlist.append(slot)
		slots_by_venue[venue] = vlist

	for venue in slots_by_venue.keys():
		tgroups = warhorn2mustard(slots_by_venue[venue])
		games = [x for x in tgroups if not x.is_admin_signup()]
		admin = [x for x in tgroups if x.is_admin_signup()]
		data = seat_table_groups(games)
		data['venue'] = venue
		data['admin'] = admin 
		fname = "Signup for %s.html" % venue
		out = output.Render(data, 'signup')
		with open(fname, "w") as fout:
			fout.write(out)

main()



