from flask import Flask, request, Response
from flask_cors import CORS

from twilio.twiml.voice_response import Dial, VoiceResponse
from twilio.rest import Client

from pysondb import db

import asyncio
import random
import string
import requests
import os
import json

twilio_account_sid = os.environ['TWILIO_ACCOUNT_SID']
twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_client = Client(twilio_account_sid, twilio_auth_token)

deepgram_api_key = os.environ['DEEPGRAM_API_KEY']

twilio_central_number = os.environ['TWILIO_CENTRAL_NUMBER']
codes = {}

recording_webhook_url = os.environ['RECORDING_WEBHOOK_URL']
incoming_webhook_url = os.environ['INCOMING_WEBHOOK_URL']

noicemail_users_db = db.getDb(os.environ['NOICEMAIL_DB'])

app = Flask(__name__)
CORS(app)

def get_user(twilio_phone_number):
    return noicemail_users_db.getBy({'twilio_phone_number': twilio_phone_number })[0]

@app.post("/incoming")
def incoming_call():
    response = VoiceResponse()
    dial = Dial(
        record='record-from-answer-dual',
        recording_status_callback = recording_webhook_url
    )

    user = get_user(request.form['To'])
    dial.number(user['physical_phone_number'])
    response.append(dial)

    return Response(str(response), 200, mimetype = 'application/xml')

@app.route("/recording", methods = ['GET', 'POST'])
async def handle_recording_webhook():
    recording_url = request.form['RecordingUrl']

    call_sid = request.form['CallSid']
    call = twilio_client.calls(call_sid).fetch()
    user = get_user(call.to)

    deepgram_result = requests.post('https://api.beta.deepgram.com/v1/listen?multichannel=true&punctuate=true&analyze_sentiment=true&detect_language=true&detect_topics=true&summarize=true&detect_entities=true', json = { "url": recording_url }, headers = { 'Content-Type':'application/json', 'Authorization': 'Token {}'.format(deepgram_api_key) })

    print(deepgram_result.content)
    deepgram_result = json.loads(deepgram_result.content)

    initial_message = "New voicemail from: " + call.from_
    twilio_client.messages.create(body = initial_message, from_ = twilio_central_number, to = user['physical_phone_number'])

    # send the sms messages (note: ignoring the returned values of the functions)
    # report the detected language
    if user['detect_language']:
        detected_language = deepgram_result['results']['channels'][0]['detected_language']
        detect_language_message = 'Language of voicemail: ' + detected_language
        twilio_client.messages.create(body = detect_language_message, from_ = twilio_central_number, to = user['physical_phone_number'])

    # report the transcript
    if user['transcribe']:
        transcript = deepgram_result['results']['channels'][0]['alternatives'][0]['transcript']
        transcribe_message = 'Voicemail transcript: ' + transcript
        twilio_client.messages.create(body = transcribe_message, from_ = twilio_central_number, to = user['physical_phone_number'])

    # report the sentiment analysis
    if user['analyze_sentiment']:
        sentiment_segments = deepgram_result['results']['channels'][0]['alternatives'][0]['sentiment_segments']
        negative = 0
        neutral = 0
        positive = 0
        for sentiment_segment in sentiment_segments:
            if sentiment_segment['sentiment'] == 'negative':
                negative += 1
            if sentiment_segment['sentiment'] == 'neutral':
                neutral += 1
            if sentiment_segment['sentiment'] == 'positive':
                positive += 1
        analyze_sentiment_message = 'Sentiment analysis: ' + ('\U0001F642' * positive) + ' ' + ('\U0001F610' * neutral) + ' ' + ('\U0001F641' * negative)
        twilio_client.messages.create(body = analyze_sentiment_message, from_ = twilio_central_number, to = user['physical_phone_number'])

    if user['detect_topics']:
        topics = []
        topic_objects = deepgram_result['results']['channels'][0]['alternatives'][0]['topics']
        for topic_object in topic_objects:
            for topic in topic_object['topics']:
                topics.append(topic['topic'])
        topics_message = "Topics: " + ', '.join(list(dict.fromkeys(topics)))
        twilio_client.messages.create(body = topics_message, from_ = twilio_central_number, to = user['physical_phone_number'])

    if user['summarize']:
        summaries = []
        summary_objects = deepgram_result['results']['channels'][0]['alternatives'][0]['summaries']
        for summary_object in summary_objects:
            summaries.append(summary_object['summary'])
        summaries_message = "Summary: " + ' '.join(summaries)
        twilio_client.messages.create(body = summaries_message, from_ = twilio_central_number, to = user['physical_phone_number'])

    return Response('', 200, mimetype = "application/json")

@app.route("/codes", methods = ['POST'])
async def create_code():
    # TODO: check that a user with this physical phone number doesn't already exist
    code = ''.join(random.choices(string.digits, k = 4))
    physical_phone_number = request.json['physical_phone_number']
    codes[physical_phone_number] = code

    body = "Your code to signup for noicemail is: " + code
    message = twilio_client.messages.create(body = body, from_ = twilio_central_number, to = physical_phone_number)

    return Response('', 201, mimetype = 'application/json')

@app.route("/users", methods = ['POST'])
async def create_noicemail_user():
    physical_phone_number = request.json['physical_phone_number']
    code = request.json['code']

    if physical_phone_number in codes and codes[physical_phone_number] == code:
        return Response(str(create_twilio_phone_number(physical_phone_number)), 201, mimetype = 'application/json')

    return Response('', 401, mimetype = 'application/json')

def create_twilio_phone_number(physical_phone_number):
    """ Lookup an available twilio number in the same area code as the user's physical phone number """
    """ We assume US numbers (+12223334444) """

    # create the twilio phone number
    area_code = physical_phone_number[2:5]
    local = twilio_client.available_phone_numbers('US').local.list(area_code = area_code, limit = 1)
    twilio_phone_number_friendly = local[0].friendly_name
    twilio_phone_number = local[0].phone_number

    # set up the webhook for this new twilio phone number (note: ignoring the returned value of the function)
    twilio_client.incoming_phone_numbers.create(phone_number = twilio_phone_number, voice_url = incoming_webhook_url)

    # create the noicemail user
    user = {}
    user['physical_phone_number'] = physical_phone_number
    user['analyze_sentiment'] = True
    user['detect_entities'] = True
    user['detect_language'] = True
    user['detect_topics'] = True
    user['summarize'] = True
    user['transcribe'] = True
    user['translate'] = True
    user['twilio_phone_number'] = twilio_phone_number
    noicemail_users_db.add(user)

    return twilio_phone_number_friendly

@app.route("/users/<twilio_phone_number>/settings", methods = ["POST"])
async def update_settings(twilio_phone_number):
    user = get_user(twilio_phone_number)
    body = request.json

    for prop, value in body.items():
        user[prop] = value

    noicemail_users_db.updateById(user['id'], user)

    return Response('', 200)


if __name__ == "__main__":
   app.run(debug = True)
