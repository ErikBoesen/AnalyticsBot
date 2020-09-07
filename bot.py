# Flask
from flask import Flask, request, render_template, redirect

# Other
import mebots
from threading import Thread
import requests
import os
import time
import re

# Bot components
from config import Config
from analytics import Group, groups


app = Flask(__name__)
app.config.from_object(Config)
bot = mebots.Bot("analyticsbot", os.environ.get("BOT_TOKEN"))

MAX_MESSAGE_LENGTH = 1000
PREFIX = "analytics"


# Webhook receipt and response
@app.route("/", methods=["POST"])
def receive():
    """
    Receive callback to URL when message is sent in the group.
    """
    # Retrieve data on that single GroupMe message.
    message = request.get_json()
    group_id = message["group_id"]
    # Begin reply process in a new thread.
    # This way, the request won't time out if a response takes too long to generate.
    Thread(target=reply, args=(message, group_id)).start()
    return "ok", 200


def reply(message, group_id):
    if message["sender_type"] == "user":
        if message["text"].startswith(PREFIX):
            command = message["text"][len(PREFIX):].strip().split(None, 1)
            # Reach out to MeBots to get instance data
            instance = bot.instance(group_id)
            bot_id = instance.id
            if not command:
                if group_id not in groups:
                    send("Analyzing messages. This may take a while.", bot_id)
                    groups[group_id] = Group(group_id, instance.token)
                    message_count = groups[group_id].message_count
                    send(f"{message_count} messages processed. View statistics at https://analyticsbot.herokuapp.com/analytics/{group_id}, or say `analytics leaderboard` to view a list of the top users!", bot_id)
                else:
                    send(f"View analytics for this group at https://analyticsbot.herokuapp.com/analytics/{group_id}.", bot_id)
            elif command == "leaderboard":
                try:
                    length = int(parameters.pop(0))
                except Exception:
                    length = 10
                leaders = groups[group_id].leaderboard[:length]
                for place, user in enumerate(leaders):
                    output += str(place + 1) + ". " + user["Name"] + " / Messages Sent: %d" % user["Messages"]
                    output += " / Likes Given: %d" % user["Likes"]
                    output += " / Likes Received: %d" % user["Likes Received"]
                    output += "\n"
                send(output, bot_id)
            elif command == "help":
                help_string = "--- Help ---"
                help_string += "\nSay 'analytics' to begin analyzing the current group."
                send(help_string, bot_id)


def send(text, bot_id):
    data = {
        "text": text,
        "bot_id": bot_id,
    }
    response = requests.post("https://api.groupme.com/v3/bots/post", data=data)


# Routing
@app.route("/analytics/<group_id>")
def show_analytics(group_id):
    # TODO: clear up users/leaderboards naming
    users = groups[group_id].users
    return render_template("analytics.html", users=users)
