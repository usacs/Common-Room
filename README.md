# Common Room

![Fat Lady from Harry Potter](static/CommonRoom.png)

An attendance system for USACS meetings.

## About
This application is built with Flask, Twilio, and simple Myjson store as the database.

### Anatomy of the Project

- /
    - common_room.py
    - static
        - style.css
        - logo
    - templates
        - index.html
        - password.html


### Dependencies
The application uses the following dependencies:

* Flask (`pip install flask`)
* The requests library. (`pip install requests`)
* Twilio (`pip install twilio`)

### Setup
You're going to need to set a few values:

* SECRET_KEY (common_room.py, line 7) - you can set this by using the `os` Python library and calling `os.urandom(24)` to get a secret key (this is used as a dependency for the Flask session to keep track of conversations with new users.)

* db (common_room.py, line 10) - you can set this by going to [myjson.com](http://myjson.com/), setting the file to `{}`, hitting the save button, and setting that as the value of db.


## How It Works

### Package Imports

* From the Flask library, we need the Flask (duh), request (gets posted values), session (keeps track of new user conversations), and render_template (renders pages with data) modules. `from flask import Flask, request, session, render_template`
* We need the whole requests package. `import requests`
* From Twilio, we need the TWIML response engine `from twilio.twiml.messaging_response import Message, MessagingResponse`

### Setup

* SECRET_KEY - to keep track of conversations with new users.
* db - URL for Myjson store for user data.
* codeword - Base codeword that can / will be changed later.
* Some basic app setup / config for Flask

### Front Page
```python
@app.route('/')
def render_homepage():
    db_request = requests.get(db).json()  # JSON data
    print(db_request)
    return render_template("index.html", page = db_request)

```

This makes an GET call to the DB, and renders a table on the front page with user data in index.html as so:

```html
<table>     
    <tr>
        <th>Number</th>
        <th>Name</th>
        <th>Graduating Class</th>
        <th>Number of Meetings</th>
    </tr>

    {% for key in page %}

        <tr>
            <td> {{ key }} </td>
            <td> {{ page[key]["name"] }} </td>
            <td> {{ page[key]["year"] }} </td>
            <td> {{ page[key]["numMeetings"] }} </td>
        </tr>

    {% endfor %}

</table>
```

### Codeword Page - Rendering
```python
@app.route('/codeword')
def render_codeword():
    return render_template("password.html", cw = codeword)
```

This renders a page with the codeword defined in setup.

### Codeword Page - Changing the Codeword.
```python
@app.route('/codeword', methods=['POST'])
def changeCode():
    new = request.form['text']
    global codeword 
    codeword = new
    print(codeword)
    return render_template("password.html", cw = codeword)
```

This grabs a value from a text box (which contains the new codeword the user wants to set), and sets the global codeword to that value. It then re-renders the codeword page with that value.


### Twilio Handlers

#### Setup
```python
number = request.form['From']  # Number Texted
message_body = request.form['Body']  # Message Body
db_request = requests.get(db).json()  # JSON data for checks.
    
resp = MessagingResponse()  # Messaging client
counter = session.get('counter', 0)  # Establish session counter
```
* Saves the user's phone number
* Saves the user's the text message they sent
* Makes a GET call to the db 
* Establishes the Twilio messaging client (`resp`)
* Establishes session counter for user.

#### Handling Existing Users
```python
if number in db_request:  # The user has already texted this number.

    # Manipulate JSON, push to DB.
    user = db_request[number]

    if message_body == codeword:  # Check that the event code is correct. If it is...
        user["numMeetings"] += 1
        post = requests.put(db, json = db_request)
        resp.message("Thanks! You've been to {} meetings".format(user["numMeetings"]))  # Let them know their attendance has been recorded.

    else:  # Ask them to try again.
        resp.message("Sorry, that was the incorrect code, please try again.")

```
Checks if the user's phone number is already in the DB. 
* If it is, it checks if they texted in the correct codeword for that meeting 
    * If it is, increases the number of meetings field for a user by one, and updates it on the DB.
    * Replies to the user with the number of meetings they've been to by that point. 
* If the password is wrong, it asks them to try again.

#### Handling New Users
```python
 else:  # Create a new entry in the DB.

    if counter == 0:  # If this is the first message ever received from the user... 

        # Ask them for their personal info.
        message = """This is your first USACS Meeting! Please send the following information:
        Your Name
        Your Graduating Class"""

        resp.message(message)

        # Increment Session
        counter += 1
        session['counter'] = counter

    else:  # If we've already asked for their personal info...

        user_data = message_body.split("\n")  # Parse it.

        # Manipulate JSON, push to DB.
        db_request[number] = {"name": user_data[0], "year": user_data[1], "numMeetings": 1}
        post = requests.put(db, json = db_request)

        resp.message("Thanks! You've been to {} meetings".format(user["numMeetings"]))  # Let them know their attendance has been recorded.
```
At this point, the user is not already in the DB. 
* Check if counter is 0 (i.e. this is the first message that the user has ever sent the Twilio number.) 
    * If it is, ask them to text back with their personal info.
* Check if the counter is greater than zero (i.e. they've already texted the number). If it is, but their number isn't in the DB yet, it's safe to assume that this message has their personal information.
    * Parse the user's text message and create a new database entry for them.
    * Sets number of attended meetings to 1.
    * Text the user and confirms that they're all set up.