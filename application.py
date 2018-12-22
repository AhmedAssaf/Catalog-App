from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalogdb_setup import Base, Category, Item, User
from sqlalchemy.pool import SingletonThreadPool
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from flask import jsonify


# Instance, every time it runs create instance name
app = Flask(__name__)
engine = create_engine(
    'sqlite:///catalog.db?check_same_thread=False',
    poolclass=SingletonThreadPool)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        logedUser = 'Current user is already connected.'
        response = make_response(json.dumps(logedUser), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['user_id']
        return response
    else:
        failMsg = 'Failed to revoke token for given user.'
        response = make_response(json.dumps(failMsg, 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Main Route Has All Categories
@app.route('/')
def showCatalog():
    categoryList = session.query(Category).all()
    itemList = session.query(Item).order_by(Item.id.desc()).limit(4)
    return render_template(
        'catalog.html',
        categoryList=categoryList,
        latestItemList=itemList)


@app.route('/Catalog.json/<string:catName>/<string:itemName>')
def showItemJson(catName, itemName):
    if 'username' not in login_session:
        return jsonify({'error': 'You are not authorized'})
    item = session.query(Item).filter_by(name=itemName).one()
    return jsonify({'item': item.serialize})


@app.route('/Catalog.json')
def showCatalogJson():
    if 'username' not in login_session:
        return jsonify({'error': 'You are not authorized'})
    categoryList = session.query(Category).all()
    return jsonify(
        {'categoryList': [dict(
            {"Category": i.serialize}) for i in categoryList]})


# Categories page
@app.route('/Catalog/<string:catName>', methods=['GET', 'POST'])
def showCategory(catName):
    allList = session.query(Category)
    categoryList = allList.all()
    itemList = allList.filter_by(name=catName).one().items
    return render_template(
        'categoryItems.html',
        categoryList=categoryList,
        ItemList=itemList)


# Items page
@app.route(
    '/Catalog/<string:catName>/<string:itemName>',
    methods=['GET', 'POST'])
def showItem(catName, itemName):
    item = session.query(Item).filter_by(name=itemName).one()
    if 'username' not in login_session:
        return render_template('itemReadOnly.html', item=item)
    else:
        if login_session['user_id'] != item.user_id:
            return render_template('itemReadOnly.html', item=item)
        else:
            return render_template('item.html', item=item)


# Item details page
@app.route('/Catalog/<string:catName>/add', methods=['GET', 'POST'])
def addItem(catName):
    cat = session.query(Category).filter_by(name=catName).one()
    if request.method == 'POST':
        if 'username' not in login_session:
            return redirect('/login')
        newItem = Item(
            name=request.form['name'],
            desc=request.form['desc'],
            category_id=cat.id,
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("New Item has been added")
        return redirect(url_for('showCategory', catName=catName))
    else:
        return render_template('addItem.html', category=cat)


# Item Edit Page
@app.route(
    '/Catalog/<string:catName>/<string:itemName>/edit',
    methods=['GET', 'POST'])
def editItem(catName, itemName):
    if 'username' not in login_session:
        return redirect('/login')
    catList = session.query(Category).all()
    editItem = session.query(Item).filter_by(name=itemName).one()
    if login_session['user_id'] != editItem.user_id:
        return """
        <script>
        function myFunction()
        {alert('You are not authorized to edit this item.');}
        </script><body onload='myFunction()'>
        """
    if request.method == 'POST':
        if request.form['categoryName']:
            editcat = session.query(Category).filter_by(
                name=request.form['categoryName']).one()
            editItem.category_id = editcat.id
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['desc']:
            editItem.desc = request.form['desc']
        session.add(editItem)
        session.commit()
        flash("Item info have been updated")
        return redirect(url_for('showCategory', catName=catName))
    else:
        return render_template('editItem.html', catList=catList, item=editItem)


# Item Delete Page
@app.route(
    '/Catalog/<string:catName>/<string:itemName>/delete',
    methods=['GET', 'POST'])
def deleteItem(catName, itemName):
    if 'username' not in login_session:
        return redirect('/login')
    cat = session.query(Category).filter_by(name=catName).one()
    deleteItem = session.query(Item).filter_by(name=itemName).one()
    if login_session['user_id'] != deleteItem.user_id:
        return """
        <script>
        function myFunction()
        {alert('You are not authorized to delete this item.');}
        </script>
        <body onload='myFunction()'>
        """
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash("Item has been deleted")
        return redirect(url_for('showCategory', catName=catName))
    else:
        return render_template('deleteItem.html', item=deleteItem)

# Main part runs if there is no exceptions, from python interpretur
if __name__ == '__main__':
    app.secret_key = 'super_secure'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
