import json
from flask import Response, request, jsonify, url_for
from app import app, celery
import requests
from datetime import datetime
import logging

from parse_top_stats_tools import *
from io_helper import get_total_fight_duration_in_hms, write_to_json
import parser_configs.parser_config_detailed as parser_config
config = fill_config(parser_config)
json_output_filename = "top_stats_detailed.json"

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler = logging.FileHandler('json.log')
handler.setFormatter(formatter)
log = logging.getLogger('json_logger')
log.setLevel(logging.INFO)
log.addHandler(handler)


def flask_logger():
        with open("json.log") as log_info:
            for line in log_info.readlines():
                yield line

        
@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = get_json_data.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

@app.route('/log-stream', methods=['GET'])
def log_stream():
    return Response(flask_logger(), mimetype="text/plain", content_type="text/event-stream")


@app.route('/json', methods=['POST'])
def retrieve_data():
    if request.method == 'POST':
        if 'links' in request.json:
            links = request.json['links']
            print(f'LINK: {links}')
            #with open('logs.txt', 'w') as log:
            try:
                log.info(f'{datetime.now()} || PROCESSING DATA ')
                #json_dict = get_json_data(links)
                task = get_json_data.delay(json_links=links)
                log.info(f'{datetime.now()} || DONE PROCESSING DATA ')
                print('Sending back data')
                print('Task', task.id)
                return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}
            except Exception as e:
                log.error(f'{datetime.now()} || ERROR ')
                log.error(f'{datetime.now()} || {e}')
                print(e)
                return {'Error': f'{e}'}
        return {'msg': 'No links'}
    else:
        print('No POST request')
        return {'msg':'No POST request'}


@celery.task(name='apps.get_json_data',bind=True)
def get_json_data(self,json_links):
    print('get_json_data')
    if json_links is None:
        return
    print('links', json_links)

    # log = open("log_detailed.txt","w")
    #log = ''
    parser_config = importlib.import_module("parser_configs.parser_config_detailed" , package=None) 
    config = fill_config(parser_config)

    print_string = "Considering fights with at least "+str(config.min_allied_players)+" allied players and at least "+str(config.min_enemy_players)+" enemies that took longer than "+str(config.min_fight_duration)+" s."
    log.info(f'{datetime.now()} || {print_string} ')
    print(print_string)

    players, fights, found_healing, found_barrier = collect_stat_data(json_links, config, log)
    if (not fights) or all(fight.skipped for fight in fights):
        myprint(log, "Aborting!", "info")
        exit(1)

    # print overall stats
    overall_squad_stats = get_overall_squad_stats(fights, config)
    overall_raid_stats = get_overall_raid_stats(fights)
    total_fight_duration = get_total_fight_duration_in_hms(overall_raid_stats['used_fights_duration'])

    num_used_fights = overall_raid_stats['num_used_fights']
        
    top_total_stat_players = {key: list() for key in config.stats_to_compute}
    top_average_stat_players = {key: list() for key in config.stats_to_compute}
    top_consistent_stat_players = {key: list() for key in config.stats_to_compute}
    top_percentage_stat_players = {key: list() for key in config.stats_to_compute}
    percentage_comparison_val = {key: 0 for key in config.stats_to_compute}

    for stat in config.stats_to_compute:
        if (stat == 'heal' and not found_healing) or (stat == 'barrier' and not found_barrier):
            continue

        top_consistent_stat_players[stat] = get_top_players(players, config, stat, StatType.CONSISTENT)
        top_total_stat_players[stat] = get_top_players(players, config, stat, StatType.TOTAL)
        top_average_stat_players[stat] = get_top_players(players, config, stat, StatType.AVERAGE)            
        top_percentage_stat_players[stat],percentage_comparison_val[stat] = get_top_percentage_players(players, config, stat, num_used_fights, top_consistent_stat_players[stat])


    json_dict = write_to_json(overall_raid_stats, overall_squad_stats, fights, players, top_total_stat_players, top_average_stat_players, top_consistent_stat_players, top_percentage_stat_players)
 
    #print_string = get_fights_overview_string(fights, overall_squad_stats, config)
    print(f'Raid data retrieved')
    self.update_state(state='PROGRESS',
                        meta={'current': len(json_links), 'total': len(json_links),
                            'status': 'Done'})
    log.info(f'{datetime.now()} || Raid data retrieved ')
    return {'current': len(json_links), 'total': len(json_links), 'status': 'Task completed!',
            'result': json_dict}
    return json_dict