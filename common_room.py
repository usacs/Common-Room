from flask import Flask, request, session, render_template
import requests
from twilio.twiml.messaging_response import Message, MessagingResponse

# Setup
SECRET_KEY = ''
app = Flask(__name__)
app.config.from_object(__name__)
db = ""
codeword = "Yee Yee Juice"


# ===============================================================================================


# This Will Be Where Attendance Data is Rendered
@app.route('/')
def render_homepage():
    db_request = requests.get(db).json()  # JSON data
    print(db_request)
    return render_template("index.html", page=db_request)


# ===============================================================================================

# This Will Be Where the Change Codeword Page is Rendered
@app.route('/codeword')
def render_codeword():
    return render_template("password.html", cw=codeword)


# This Will Be Where Change Codeword Event is Handled
@app.route('/codeword', methods=['POST'])
def changeCode():
    new = request.form['text']
    global codeword
    codeword = new
    print(codeword)
    return render_template("password.html", cw=codeword)


# ===============================================================================================


# This Will Be How Messages Are Handled
@app.route('/sms', methods=['POST'])
def sms():
    # Setup
    number = request.form['From']  # Number Texted
    message_body = request.form['Body']  # Message Body
    db_request = requests.get(db).json()  # JSON data for checks.

    resp = MessagingResponse()  # Messaging client
    counter = session.get('counter', 0)  # Establish session counter
    #counter == 3 means the user is done configuring thier personal information
    if number in db_request & counter == 3:  # The user has already texted this number and their personal info is correct

        # Manipulate JSON, push to DB.
        user = db_request[number]

        if message_body == codeword:  # Check that the event code is correct. If it is...
            user["numMeetings"] += 1
            post = requests.put(db, json=db_request)
            resp.message("Thanks! You've been to {} meetings".format(
                user["numMeetings"]))  # Let them know their attendance has been recorded.

        else:  # Ask them to try again.
            resp.message("Sorry, that was the incorrect code, please try again.")


    else:  # Create a new entry in the DB.

        if counter == 0:  # If this is the first message ever received from the user... 

            # Ask them for their personal info.
            message = """This is your first USACS Meeting! Please send the following information
            In one Text, seperated by spaces:
            Your Name, first and last
            Your Graduating Class"""

            resp.message(message)

            # Increment Session
            counter += 1
            session['counter'] = counter

        else:  # If we've already asked for their personal info...

            if(counter == 1): #we currently have their personal info
                user_data = message_body.split(" ")  # Parse it.
                name = user_data[0] + "_" + user_data[1]
                year = user_data[2]


                # Manipulate JSON, push to DB.
                db_request[number] = {"name": user_data[0] + "_" + user_data[1], "year": user_data[2], "numMeetings": 1}
                post = requests.put(db, json=db_request)

                #increment session
                counter += 1
                session['counter'] = counter

                #ask if information was parsed correctly
                resp.message("Is your information:\n Name: " + user_data[0] + "_" + user_data[1] +
                         "\n year:" + user_data[2]  + "\n correct? (yes/no)")

            if(counter == 2): #we are checking to ensure the user's information was parsed correctly

                messageAccepted = False
                #the user is happy with their information
                if(message_body.lower() == "yes" | message_body.lower() == "y" | message_body.lower() == "ye"):

                    # increment session
                    counter += 1
                    session['counter'] = counter

                    user = db_request[number]

                    resp.message("Thanks! You've been to {} meetings".format(
                    user["numMeetings"]))  # Let them know their attendance has been recorded.

                    messageAccepted = True
                #information was not parsed correctly
                if(message_body.lower() == "no" | message_body.lower == "n"):
                    resp.message("That is ok, text again to restart the process")
                    messageAccepted = True
                    session['counter'] = 0

                if(not messageAccepted):
                        resp.message("that response was not understood, valid responses are 'yes' or 'no'\n"
                                     "please respond again")


    return str(resp)


# ===============================================================================================


if __name__ == '__main__':
    app.run()
