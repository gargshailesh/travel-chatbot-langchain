from flask import Flask, render_template, request, redirect, session, abort
import os, pathlib, requests, json
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
from pip._vendor import cachecontrol
from travel_bot import TravelBot
from functools import wraps

app = Flask(__name__)
# Initializing secret is important other wise Flask will error out
app.secret_key = "abc123"

# GOOGLE_CLIENT_ID, REDIRECT_URI, client_secrets_file  is required for Google Auth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
REDIRECT_URI=os.getenv("REDIRECT_URI")
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "google_client_secret.json")

# As this is a POC disabling https, should not be done for production usecases
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri=REDIRECT_URI
)

'''
    This function validates whether user is authenticalted or not
    By checking email in session
'''
def login_is_required(function):
    @wraps(function)  
    def wrapper(*args, **kwargs):
        if 'email' not in session:
            return abort(401)
        else:
            return function(*args, **kwargs)
    return wrapper

'''
    Call this method to clear user the chat history of the user
'''
@app.route('/clear_session')
def clear_session():
    # Clear the session
    print("Got in clear_session...")
    user_id = session["email"] 
    if (user_id == None):
        #Redirect the user to login page
        return redirect('/login')
    
    tbot = TravelBot(user_id=user_id)

    tbot.chat_history_from_firestore.clear()
    return redirect('/chat')

@app.route('/login')
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")
   
@app.route('/chat', methods=['POST','GET'])
@login_is_required
def protected_area():
    #return "You are authorised to chat"
    user_id = session["email"] 
    if (user_id == None):
        #Redirect the user to login page
        return redirect('/login')
    
    tbot = TravelBot(user_id=user_id)
    
    if request.method == 'POST':
        user_input = request.form['user_text']
        messages = tbot.generate_ai_response(user_message=user_input)
    else:
        # User is calling get, it means we need to load chat history from the DB
        messages = tbot.load_chat_history_from_firestore()

        #If the last message is from User, 
        # we need to 1st generate response for last message 
        # and return the whole chat history from the database
        if messages[-1].type == 'human':
            messages = tbot.generate_ai_response(user_message=None)

    # Summary is null as user is still chattting with Bot
    return render_template('index.html', messages=messages, summary=None)
    
'''
    To be called when user wants to summarize the chat history
    summary is expected to be in json
    but sometime LLM can send response other than json 
    or mixed, i.e. text & json
'''
@app.route('/summarize')
@login_is_required
def summarize():
    user_id = session["email"] 
    if (user_id == None):
        #Redirect the user to login page
        return redirect('/login')
    
    tbot = TravelBot(user_id=user_id)
    messages = tbot.load_chat_history_from_firestore()
    summary = tbot.summarize_chat_history()
    return render_template("index.html", messages=messages, summary=beautify_json(summary))


'''
    This is called by Google if user is authenticated successfully !
'''
@app.route('/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    return redirect("/chat")

@app.route('/',  methods=['POST','GET'])
def index():
    if 'email' not in session:
        return render_template('login.html')
    else:
        return redirect('/chat')
    
def beautify_json(json_data):
    """Beautifies JSON data by indenting and adding new lines.

    Args:
        json_data (str): The JSON data as a string.

    Returns:
        str: The beautified JSON data as a string.
    """

    try:
        # Load the JSON data into a Python object
        data = json.loads(json_data)

        # Convert the object back to a JSON string with indentation
        formatted_json = json.dumps(data, indent=4, separators=(',', ': '))

        # Add a newline after each key
        lines = formatted_json.splitlines()
        formatted_json = '\n'.join(line.replace(',', ',\n') for line in lines)

        return formatted_json
    except json.JSONDecodeError as e:
        # Handle JSON decoding errors gracefully
        print(f"Error decoding JSON: {e}")
        return json_data

# Setting debug=True as it is a POC
# Should not be the case if it is a production project
if __name__ == "__main__":
    app.run(debug=True)