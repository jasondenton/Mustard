from datetime import datetime
from copy import copy
import re

from mustard import Player, TableGroup

warhorn_campaign = {
	"D&D Adventurers League" : "DCI",
	"Starfinder Society" : "Pathfinder Societ",
	"Pathfinder Society (1st edition)" : "Pathfinder Societ"
}

TS_FMT = "%Y-%m-%dT%H:%M:%S%z"
ROLE_REGEX = re.compile("([\w|\?]+)( \d+)?")

def strip_chrs(st):
	nst = ''
	for c in st:
		if c == "'" or c == "(" or c == ')' or c == '[' or c == ']' or c == '#':
			continue
		nst = nst + c 
	return nst.strip()

def parse_name(name):
	team = None
	family = None
	hash_pos = name.rfind('#')
	curve_pos = name.rfind('(')
	sq_pos = name.rfind('[')
	team_pos = max(hash_pos, curve_pos, sq_pos)
	if team_pos > -1:
		team = strip_chrs(name[team_pos:])
		name = name[:team_pos].strip()
	else:
		team = None
	fpos = name.rfind(' ')
	if fpos > -1:
		family = strip_chrs(name[fpos:])
	else:
		family = None
	if not team and family:
		team = '__remove__%s' % family
	return (name, team)
	
def warhorn_player(p, network):
	player = Player()
	(player.name, player.team) = parse_name(p['name'])
	if player.team and player.team[0:10] == '__remove__':
		player.print_team = None
	else:
		player.print_team = player.team
	player.signup_at =  datetime.strptime(p['signed_up_at'], TS_FMT)
	player.email = p['email']
	player.role = None
	for mb in p['organized_play_memberships']:
	    if mb['network'] == network:
	        player.number = mb['member_number']
	        break
	player.level = 0
	player.roles = [] 
	if p.get('character', None) and p['character']['classes']:
		for c in p['character']['classes']:
			(cl,lv) = ROLE_REGEX.match(c).groups()
			if not player.role and cl and cl != '?':
				player.role = cl
			else:
				player.role = None
			if lv: lv = int(lv) 
			else: 0
			player.add_role(cl,lv)
	return player
	   
def list_of_players(lst, campaign):
	plst = []
	for p in lst:
		plst.append(warhorn_player(p, campaign))
	if plst: plst.sort(key=lambda x:x.signup_at)
	return plst

def warhorn2mustard(data):
	sessions = []
	for slot in data:
		start_time = datetime.strptime(slot['starts_at'], TS_FMT)
		end_time = datetime.strptime(slot['ends_at'], TS_FMT)
		uuid = slot['uuid']
		for session in slot['sessions']:
			sc = session['scenario']
			tg = TableGroup(sc['game_system'])
			tg.start_time = start_time
			tg.end_time = end_time
			tg.uuid = [uuid,session['uuid']]
			tg.event = sc['name']
			tg.description = sc['blurb']
			tg.pass_through['min_level'] = sc['min_level']
			tg.pass_through['max_level'] = sc['max_level']
			tg.tables = session['table_count']
			tg.seats_per_table = session['table_size']
			tg.gmlist = []
			tg.gmlist = list_of_players(session['gms'], warhorn_campaign[sc['campaign']])
			tg.players = list_of_players(session['players'], warhorn_campaign[sc['campaign']])
			sessions.append(tg)
	return sessions