from flask import Flask, render_template, request
import openai
import spotipy
import joblib
import spotipy.util as util
import random
from moodtape_functions import authenticate_spotify, aggregate_top_artists, aggregate_top_tracks, select_tracks, create_playlist

client_id = 'fe950c4faf544e42af36cfa40473ccd3'
client_secret = 'c37d08196f3644a081b8dd97854e2be7'
redirect_uri = 'https://example.com/callback/'
scope = 'user-library-read user-top-read playlist-modify-public user-follow-read'

messages = [{'role': 'system',
             'content': 'Act as a chat bot that asks questions to understand the mood of the user and reply accordingly. if the user deviates and asks other questions not related to their mood, bring the user back to this and Keep asking questions about the users current mood. Keep the converstion only until the mood is clear or the user seems done chatting.'}]

app = Flask(__name__)

# Set up OpenAI API credentials
openai.api_key = "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"

global chat
chat = ''
# Define the default route to return the index.html file


@app.route("/")
def index():
    return render_template("index.html")

# Define the /api route to handle POST requests


@app.route("/api", methods=["POST"])
def api():
    global chat
    # Get the message from the POST request
    message = request.json.get("message")
    # Send the message to OpenAI's API and receive the response
    chat = chat+' ' + message
    mess = {'role': 'user', 'content': message}
    messages.append(mess)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    print(messages)
    print(chat)
    if completion.choices[0].message != None:
        # messages.append(dict(completion.choices[0].message))
        return completion.choices[0].message

    else:
        return 'Failed to Generate response!'


@app.route('/songs')
def my_form():
    return render_template('input.html')


@app.route("/songs", methods=['POST'])
def moodtape():
    pipe_lr = joblib.load(
        open("emotion_classifier_pipe_lr_03_june_2021_navya.pkl", "rb"))
    #ex1 = "i love my poccha"
    #chat = 'You are just trying to make me angry.What is wrong with you?You are going to regret this'
    mood = pipe_lr.predict([chat])[0]
    print(mood)
    username = request.form['username']
    token = util.prompt_for_user_token(
        username, scope, client_id, client_secret, redirect_uri)
    spotify_auth = authenticate_spotify(token)
    top_artists = aggregate_top_artists(spotify_auth)
    top_tracks = aggregate_top_tracks(spotify_auth, top_artists)
    selected_tracks = select_tracks(spotify_auth, top_tracks, mood)

    random.shuffle(selected_tracks)
    # print(selected_tracks)
    return render_template('songs.html', track_ids=selected_tracks[0:25])


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8000)
