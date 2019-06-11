#!/usr/local/bin/python3

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
	fout_name = sys.argv[2]
	pp = PrettyPrinter()
	output = AutoMusterTemplateEngine()

	with open(fin_name) as fin:
		top = json.load(fin)
	slots = top['slots']
	tgroups = warhorn2mustard(slots)
	data = seat_table_groups(tgroups)

	out = output.Render(data, 'signup')
	with open(fout_name, "w") as fout:
		fout.write(out)

main()


