from flask import Flask, request, Response
from twilio.twiml.voice_response import Dial, VoiceResponse
from twilio.rest import Client

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

twilio_central_number = '+15133275732'
codes = {}
noicemail_users = {}

recording_webhook_url = 'https://noicemail.deepgram.com/recording'
incoming_webhook_url = 'https://noicemail.deepgram.com/incoming'

# TODO: do this with a real database, or via the twilio api (or both)
def initialize_noicemail_users():
    noicemail_users['+17346362092'] = {}
    noicemail_users['+17346362092']['physical_phone_number'] = '+17344787181'
    noicemail_users['+17346362092']['analyze_sentiment'] = True

initialize_noicemail_users()

app = Flask(__name__)
@app.post("/incoming")
def incoming_call():
    response = VoiceResponse()
    dial = Dial(
        record='record-from-answer-dual',
        recording_status_callback = recording_webhook_url
    )

    dial.number(noicemail_users[request.form['To']]['physical_phone_number'])
    response.append(dial)

    return Response(str(response), 200, mimetype = 'application/xml')

@app.route("/recording", methods = ['GET', 'POST'])
async def handle_recording_webhook():
    recording_url = request.form['RecordingUrl']

    call_sid = request.form['CallSid']
    call = twilio_client.calls(call_sid).fetch()

    deepgram_result = requests.post('https://api.beta.deepgram.com/v1/listen?multichannel=true&punctuate=true&analyze_sentiment=true&detect_language=true&detect_topics=true&summarize=true&detect_entities=true', json = { "url": recording_url }, headers = { 'Content-Type':'application/json', 'Authorization': 'Token {}'.format(deepgram_api_key) })

    print(deepgram_result.content)
    deepgram_result = json.loads(deepgram_result.content)

    # send the sms messages (note: ignoring the returned values of the functions)
    # report the detected language
    detected_language = deepgram_result['results']['channels'][0]['detected_language']
    print(detected_language)
    twilio_client.messages.create(body = detected_language, from_ = twilio_central_number, to = noicemail_users[call.to]['physical_phone_number'])

    # report the transcript
    transcript = deepgram_result['results']['channels'][0]['alternatives'][0]['transcript']
    print(transcript)
    twilio_client.messages.create(body = transcript, from_ = twilio_central_number, to = noicemail_users[call.to]['physical_phone_number'])

    # report the sentiment analysis
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
    sentiment_message = 'positive: ' + str(positive) + '; neutral: ' + str(neutral) + '; negative: ' + str(negative)
    print(sentiment_message)
    twilio_client.messages.create(body = sentiment_message, from_ = twilio_central_number, to = noicemail_users[call.to]['physical_phone_number'])

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
    noicemail_users[twilio_phone_number] = {}
    noicemail_users[twilio_phone_number]['physical_phone_number'] = physical_phone_number
    noicemail_users[twilio_phone_number]['analyze_sentiment'] = True

    return twilio_phone_number_friendly

if __name__ == "__main__":
   app.run(debug = True)
