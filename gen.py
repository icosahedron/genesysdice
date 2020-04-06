import json
import re
import random
import base64
from urllib.parse import *

# These values are from anydice.com https://anydice.com/program/dd67 that simulate the Genesys dice.
# They haven't been verified for accuracy (yet)

# B: 2 \ # of boost die \
# S: 0 \ # of setback die \
# A: 1 \ # of ability die \
# D: 3 \ # of difficulty die \
# P: 3 \ # of proficiency die \
# C: 0 \ # of challenge die \

# \ Success and Failure Faces \ 
# BOOS: {0, 0, 1, 1, 0, 0}
# ABIS: {0, 1, 1, 2, 0, 0, 1, 0}
# PROS: {0, 1, 1, 2, 2, 0, 1, 1, 1, 0, 0, 1}
# SETF: {0, 0, 1, 1, 0, 0}
# DIFF: {0, 1, 2, 0, 0, 0, 0, 1}
# CHAF: {0, 1, 1, 2, 2, 0, 0, 1, 1, 0, 0, 1}

# \ Advantage and Threat Faces \
# BOOA: {0, 0, 0, 1, 2, 1}
# ABIA: {0, 0, 0, 0, 1, 1, 1, 2}
# PROA: {0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 0}
# SETT: {0, 0, 0, 0, 1, 1}
# DIFT: {0, 0, 0, 1, 1, 1, 2, 1}
# CHAT: {0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 0}

# \ Triumph and Despair \
# PROT: {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1}
# CHAD: {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1}

# SUCCESSES: BdBOOS + AdABIS + PdPROS - SdSETF - DdDIFF - CdCHAF
# ADVANTAGES: BdBOOA + AdABIA + PdPROA - SdSETT - DdDIFT - CdCHAT

# output SUCCESSES named "Successes"
# output ADVANTAGES named "Advantages"
# output PdPROT named "Triumphs"
# output CdCHAD named "Despairs"

dice_names = { 
    'B' : 'Boost', 
    'S' : 'Setback',
    'A' : 'Ability',
    'D' : 'Difficulty',
    'P' : 'Proficiency',
    'C' : 'Challenge' }

symbol_names = {
    '' : 'Blank',
    'S': 'Success',
    'F': 'Failure',
    'A': 'Advantage',
    'T': 'Threat',
    'SR': 'Success & Triumph',
    'FD': 'Failure & Despair',
    'AA': '2 x Advantage',
    'SS': '2 x Success',
    'FF': '2 x Failure',
    'TT': '2 x Threat',
    'SA': 'Success & Advantage',
    'FT': 'Failure & Threat'
}

PIPS = {
    "B" : ["", "", "S", "SA", "AA", "A"], 
    "A" : ["", "S", "S", "SS", "A", "A", "SA", "AA"], 
    "P" : ["", "S", "S", "SS", "SS", "A", "SA", "SA", "SA", "AA", "AA", "SR"], 
    "S" : ["", "", "F", "F", "T", "T"], 
    "D" : ["", "F", "FF", "T", "T", "T", "TT", "FT"], 
    "C" : ["", "F", "F", "FF", "FF", "T", "T", "FT", "FT", "TT", "TT", "FD"]
}

def lambda_handler(event, context):
    
    body = event['body']
    form = parse_qs(str(base64.b64decode(body)))
    dice_text = form['text'][0]
    
    err_text = ''
    for e in re.finditer('([^ABCDSP\s]\w+)', dice_text):
        err_text += "Unknown dice type {}\n".format(e.group(0))
    if len(err_text) > 0:
        return {
            'statusCode': 200,
            'headers' : { 'Content-type' : 'application/json' },
            'body': json.dumps({ 'text': err_text, 'response_type' : 'in_channel' })
        }

    dice_counts = {}
    for d in re.finditer('([ABCDSP])(\d)', dice_text):
       dice_counts[d.group(1)] = int(d.group(2))
        
    rolls = {}
    for d, c in dice_counts.items():
        rolls[d] = [PIPS[d][random.randint(0, len(PIPS[d])-1)] for x in range(c)]
        
    rolls_to_count = ''.join([''.join(r) for r in rolls.values()])
    success = rolls_to_count.count('S') - rolls_to_count.count('F')
    advantage = rolls_to_count.count('A') - rolls_to_count.count('T')
    triumph = rolls_to_count.count('R') - rolls_to_count.count('D')

    success_key = 'Successes' if success >= 0 else 'Failures'
    advantage_key = 'Advantages' if advantage >= 0 else 'Threats'
    triumph_key = 'Triumph' if triumph >= 0 else 'Despair'

    success = abs(success)
    advantage = abs(advantage)
    triumph = abs(triumph)

    results = '*Rolls*:\n'
    formatted_rolls = {}    
    for die in rolls.keys():
        formatted_rolls[dice_names[die]] = [symbol_names[roll] for roll in rolls[die]]
        results = results + '_' + dice_names[die] + '_: ' + ', '.join(formatted_rolls[dice_names[die]]) + '\n'

    results = results + '*Totals*: {} = {}, {} = {}, {} = {}'.format(success_key, success, advantage_key, advantage, triumph_key, triumph)
        
    r = { 'text' : results, 'response_type'  : 'in_channel' }

    return {
        'statusCode': 200,
        'headers' : { 'Content-type' : 'application/json' },
        'body': json.dumps(r)
    }
