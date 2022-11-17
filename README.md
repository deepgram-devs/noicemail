# noicemail

## Running

From a `tmux` session:

```bash
$ cd noicemail/backend
$ NOICEMAIL_DB="./noicemail.json" gunicorn --bind 0.0.0.0:5000 server:app
```

If the server is already running in another `tmux` session, you'll get an error
like this:

```
[2022-11-17 18:25:55 +0000] [29980] [ERROR] Connection in use: ('0.0.0.0', 5000)
```
