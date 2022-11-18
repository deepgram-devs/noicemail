# noicemail

Noicemail is the project from team "Your Mom" for the Deepgram Fall Gram Jam 2022. It consists of a frontend and a backend
service which allows users to signup with their (US) phone number. We provide them with a Twilio phone number set up to
forward calls to their (US) phone number, and if the calls go to voicemail, they will get transcribed by Deepgram
and information about the voicemail will be texted to the their (US) phone number.

## Running the backend

We are running the backend on an AWS instance (only team members have access) at https://noicemail.deepgram.com.

The backend requires the following environment variables to be set:

* TWILIO_ACCOUNT_SID: your Twilio account sid (get this from the Twilio Console)
* TWILIO_AUTH_TOKEN: your Twilio auth token (get this from the Twilio Console)
* TWILIO_CENTRAL_NUMBER: a Twilio number that will send texts to noicemail users
* DEEPGRAM_API_KEY: a Deepgram API key (get this from the Deepgram Console)
* NOICEMAIL_DB: a path to a json file that will store noicemail user information
* RECORDING_WEBHOOK_URL: the public URL where the `/recording` endpoint will live (e.g. https://noicemail.deepgram.com/recording)
* INCOMING_WEBHOOK_URL: the public URL where the `/incoming` endpoint will live (e.g. https://noicemail.deepgram.com/incoming)

Then, from a `tmux` session on the AWS instance, do:

```bash
$ cd noicemail/backend
$ gunicorn --bind 0.0.0.0:5000 server:app
```

If the server is already running in another `tmux` session, you'll get an error
like this:

```
[2022-11-17 18:25:55 +0000] [29980] [ERROR] Connection in use: ('0.0.0.0', 5000)
```

## The frontend

See `frontend/README.md` for more info about the frontend.
