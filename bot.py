# Flask
from flask import Flask, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

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
db = SQLAlchemy(app)
bot = mebots.Bot("analyticsbot", os.environ.get("BOT_TOKEN"))

MAX_MESSAGE_LENGTH = 1000
PREFIX = "analyze"


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
    send(process_message(Message(message)), group_id)


def process_message(message):
    responses = []
    if message.sender_type == SenderType.USER:
        if message["text"].startswith(PREFIX):
            instructions = message["text"][len(PREFIX):].strip().split(None, 1)
            command = instructions.pop(0).lower()
            query = instructions[0] if len(instructions) > 0 else ""
            group_id = message["group_id"]
            if group_id not in self.groups:
                self.groups[group_id] = Group(group_id)
                return f"{message_count} messages processed. View statistics at https://analyticsbot.herokuapp.com/analytics/{group_id}, or say `analytics leaderboard` to view a list of the top users!"
            if not command:
                return f"View analytics for this group at https://analyticsbot.herokuapp.com/analytics/{group_id}."
            elif command == "leaderboard":
                try:
                    length = int(parameters.pop(0))
                except Exception:
                    length = 10
                leaders = self.groups[group_id].leaderboard[:length]
                for place, user in enumerate(leaders):
                    output += str(place + 1) + ". " + user["Name"] + " / Messages Sent: %d" % user["Messages"]
                    output += " / Likes Given: %d" % user["Likes"]
                    output += " / Likes Received: %d" % user["Likes Received"]
                    output += "\n"
            else:
                return "Please state a valid command!"
            return output
            if command == "help":
                help_string = "--- Help ---"
                help_string += "\nSay 'analytics' to begin analyzing the current group."
                responses.append(help_string)
            else:
                pass
    return responses


def send(message, group_id):
    """
    Reply in chat.
    :param message: text of message to send. May be a tuple with further data, or a list of messages.
    :param group_id: ID of group in which to send message.
    """
    # Recurse when sending multiple messages.
    if isinstance(message, list):
        for item in message:
            send(item, group_id)
        return
    data = {
        "bot_id": bot.instance(group_id).id,
    }
    image = None
    if isinstance(message, tuple):
        message, image = message
    # TODO: this is lazy
    if message is None:
        message = ""
    if len(message) > MAX_MESSAGE_LENGTH:
        # If text is too long for one message, split it up over several
        for block in [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]:
            send(block, group_id)
            time.sleep(0.3)
        data["text"] = ""
    else:
        data["text"] = message
    if image is not None:
        data["picture_url"] = image
    # Prevent sending message if there's no content
    # It would be rejected anyway
    if data["text"] or data.get("picture_url"):
        response = requests.post("https://api.groupme.com/v3/bots/post", data=data)


# Routing
@app.route("/analytics/<group_id>")
def show_analytics(group_id):
    # TODO: clear up users/leaderboards naming
    users = commands["analytics"].leaderboards.get(group_id)
    return render_template("analytics.html", users=users)


# Local testing
if __name__ == "__main__":
    while True:
        print(process_message(Message(text=input("> "))))
