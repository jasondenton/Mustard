#Very simply application file for a flask based web service. Use with muster.wsgi.
#This create a single endpoint /muster, which gets warhorn data for an entire event
#posted to it, and returns the json version of the call to seat_table_gropus.

from flask import Flask, jsonify, request
app = Flask(__name__)

from mustard import init_game_data, seat_table_groups
init_game_data('/var/www/mustard/gamesystems.json')

from warhorn import warhorn2mustard

@app.route('/muster',methods=['POST'])
def muster():
	warhorn_data = request.json
	tgroups = warhorn2mustard(warhorn_data['slots'])
	data = seat_table_groups(tgroups)

	return jsonify({
		'tables' : [x.as_dict() for x in data['tables']],
		'waitlists' : [x.as_dict() for x in data['waitlists']],
		'locations_needed' : data['locations_needed'],
		'messages' : data['messages']
	})
