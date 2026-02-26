from flask import Flask, jsonify
import requests
import random
import string

app = Flask(__name__)

base = "https://api.mail.tm"


@app.route("/api", methods=["GET"])
def create_mail():

    domain = requests.get(base + "/domains").json()["hydra:member"][0]["domain"]

    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

    email = f"{username}@{domain}"

    password = "123456"

    requests.post(
        base + "/accounts",
        json={
            "address": email,
            "password": password
        }
    )

    return jsonify({
        "email": email,
        "password": password
    })


app = app
