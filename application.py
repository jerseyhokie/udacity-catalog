from models import Base, Categories, CategoryItems, User
from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, abort, g
from flask import session as login_session
from flask import make_response
from flask_httpauth import HTTPBasicAuth
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import random
import string
import requests

app = Flask(__name__)

auth = HTTPBasicAuth()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Setup Facebook Login
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type='
    'fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"

    '''
    Due to the formatting for the result from the server token exchange we
    have to split the token first on commas and select the first index which
    gives us the key : value for the server access token then we split it on
    colons to pull out the actual token value and replace the remaining quotes
    with nothing so that it can be used directly in the graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = "https://graph.facebook.com/v2.8/me?"
    "access_token=%s&fields=name,id,email" % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token='
    '%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: '
    '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token='
    '%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# Create Google Login
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
        response = make_response(json.dumps('Current user is '
                                            'already connected.'), 200)
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
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # See if the user exists, make a new on eif they do not
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;\
                border-radius: 150px;-webkit-border-radius: 150px;\
                -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user '
                                            'not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for \
            given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).first()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).first()
        return user.id
    except:
        return None


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


# JSON Web Interface
#    Establishes a way to read the catalog via JSON requests
#    Each method is found by adding /JSON
#    Entire catalog is read-only
@app.route('/catalog/JSON')
def showCatalogJSON():
    catalog = session.query(Categories).all()
    return jsonify(Catalog=[categories.serialize for categories in catalog])

# @app.route('/JSON')
# def showAllCatalogJSON():
#     jsonCatalog = ""
#     entireCatalog = []
#     catalog = session.query(Categories).all()
#     for c in catalog:
#         items = session.query(CategoryItems).filter_by(categories_id=c.id)
#         itemList = {}
#         itemList["id"] = c.id
#         itemList["name"] = c.name
#         itemList["items"] = (i.serialize for i in items)
#         entireCatalog.append(itemList)
#     return jsonify (Catalog = entireCatalog)


@app.route('/catalog/<int:categories_id>/JSON')
def showCategoryJSON(categories_id):
    categoryToShow = session.query(Categories).filter_by(
        id=categories_id).one()
    itemsToShow = session.query(CategoryItems).filter_by(
        categories_id=categoryToShow.id)
    return jsonify(Category=[categoryItems.serialize for
                             categoryItems in itemsToShow])


@app.route('/catalog/<string:categories_name>/JSON')
def showCategoryByNameJSON(categories_name):
    categoryToShow = session.query(Categories).filter_by(
        name=categories_name).one()
    itemsToShow = session.query(CategoryItems).filter_by(
        categories_id=categoryToShow.id)
    return jsonify(Category=[categoryItems.serialize for
                             categoryItems in itemsToShow])


@app.route('/catalog/<int:categories_id>/<int:categoriesItems_id>/JSON')
def showCategoryItemJSON(categories_id, categoriesItems_id):
    item = session.query(CategoryItems).filter_by(id=categoriesItems_id).one()
    return jsonify(Item=[item.serialize])


@app.route('/catalog/<string:categories_name>/'
           '<string:categoriesItems_name>/JSON')
def showCategoryItemByNameJSON(categories_name, categoriesItems_name):
    item = session.query(CategoryItems).filter_by(
        name=categoriesItems_name).one()
    return jsonify(Item=[item.serialize])


# Catalog Web Interface
#    Establishes all the CRUD operations via webpages
#    Each method is listed in CRUD order,
#        categories then categoryItems respectively
#    All methods that edit the DB are protected
#    All methods are availabel using ID or Name of item as key

# CREATE - Add a new Category to the Catalog
@app.route('/catalog/new',
           methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Categories(name=request.form['name'],
                             user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("New Category created!")
        return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html')


# READ - Root of the web app - Defaults to show all categories
@app.route('/')
@app.route('/catalog/')
def showCategories():
    categories = session.query(Categories).order_by(asc(Categories.name))
    recentCategoriesItems = session.query(
        CategoryItems).join(Categories).order_by(
        desc(CategoryItems.id)).limit(5)
    if 'username' not in login_session:
        return render_template('publicCategories.html',
                               categories=categories,
                               recent=recentCategoriesItems)
    else:
        return render_template('categories.html',
                               categories=categories,
                               recent=recentCategoriesItems)


# UPDATE - Edit a Category
# Function available with both category ID and Category Name
@app.route('/catalog/<int:categories_id>/edit',
           methods=['GET', 'POST'])
def editCategory(categories_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Categories).filter_by(id=categories_id).one()
    if editedItem.user_id != login_session['user_id']:
        flash("Edit is only available to the owner of the item!")
        return redirect(url_for('showCategories'))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('editCategory.html',
                               categories_id=categories_id,
                               item=editedItem)


@app.route('/catalog/<string:categories_name>/edit',
           methods=['GET', 'POST'])
def editCategoryByName(categories_name):
    if 'username' not in login_session:
        return redirect('/login')
    categoryNameID = session.query(Categories).filter_by(
        name=categories_name).one()
    categories_id = categoryNameID.id
    editedItem = session.query(Categories).filter_by(
        name=categories_name).one()
    if editedItem.user_id != login_session['user_id']:
        flash("Edit is only available to the owner of the item!")
        return redirect(url_for('showCategories'))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('editCategory.html',
                               categories_name=categories_name,
                               item=editedItem)


# DELETE - Remove a Category
# Function available with both category ID and Category Name
@app.route('/catalog/<int:categories_id>/delete',
           methods=['GET', 'POST'])
def deleteCategory(categories_id):
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = session.query(Categories).filter_by(
        id=categories_id).one()
    itemsToDelete = session.query(CategoryItems).filter_by(
        categories_id=categories_id)
    if categoryToDelete.user_id != login_session['user_id']:
        flash("Delete is only available to the owner of the item!")
        return redirect(url_for('showCategories'))
    if request.method == 'POST':

        # Insert code to delete items from CategoryItems with categories_id

        for i in itemsToDelete:
            session.delete(i)

        session.delete(categoryToDelete)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteCategory.html',
                               itemToDelete=categoryToDelete,
                               items=itemsToDelete,
                               categories_id=categories_id)


@app.route('/catalog/<string:categories_name>/delete',
           methods=['GET', 'POST'])
def deleteCategoryByName(categories_name):
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = session.query(Categories).filter_by(
        name=categories_name).one()
    itemsToDelete = session.query(CategoryItems).filter_by(
        categories_id=categoryToDelete.id)
    if categoryToDelete.user_id != login_session['user_id']:
        flash("Delete is only available to the owner of the item!")
        return redirect(url_for('showCategories'))
    if request.method == 'POST':

        # Code to delete items from CategoryItems with categories_id
        # This cleans up the database if you delete at category,
        # removing remnant items
        for i in itemsToDelete:
            session.delete(i)

        session.delete(categoryToDelete)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteCategory.html',
                               itemToDelete=categoryToDelete,
                               items=itemsToDelete,
                               categories_name=categories_name)


# CREATE - Add a new Category Item to a specific Category
# Function available with both category ID and Category Name
@app.route('/catalog/<int:categories_id>/new',
           methods=['GET', 'POST'])
def newCategoryItem(categories_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = CategoryItems(name=request.form['name'],
                                description=request.form['description'],
                                categories_id=categories_id,
                                user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("New Category Item added!")
        return redirect(url_for('showCategory',
                                categories_id=categories_id))
    else:
        return render_template('newCategoryItem.html',
                               categories_id=categories_id)


@app.route('/catalog/<string:categories_name>/new',
           methods=['GET', 'POST'])
def newCategoryItemByName(categories_name):
    if 'username' not in login_session:
        return redirect('/login')
    categoryNameID = session.query(Categories).filter_by(
        name=categories_name).one()
    categories_id = categoryNameID.id
    if request.method == 'POST':
        newItem = CategoryItems(name=request.form['name'],
                                description=request.form['description'],
                                categories_id=categories_id,
                                user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("New Category Item added!")
        return redirect(url_for('showCategoryByName',
                                categories_name=categories_name))
    else:
        return render_template('newCategoryItem.html',
                               categories_name=categories_name)


# READ - Display all of the items in a single Category
# Function available with both category ID and Category Name
@app.route('/catalog/<int:categories_id>/')
def showCategory(categories_id):
    categories = session.query(Categories).filter_by(id=categories_id).one()
    creator = getUserInfo(categories.user_id)
    items = session.query(CategoryItems).filter_by(
        categories_id=categories_id)
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('showPublicCategory.html',
                               categories=categories,
                               items=items,
                               categories_id=categories_id,
                               creator=creator)
    else:
        return render_template('showCategory.html',
                               categories=categories,
                               items=items,
                               categories_id=categories_id,
                               creator=creator)


@app.route('/catalog/<string:categories_name>/')
def showCategoryByName(categories_name):
    categories = session.query(Categories).filter_by(
        name=categories_name).one()
    creator = getUserInfo(categories.user_id)
    items = session.query(CategoryItems).filter_by(
        categories_id=categories.id)
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('showPublicCategory.html',
                               categories=categories,
                               items=items,
                               categories_name=categories_name,
                               creator=creator)
    else:
        return render_template('showCategory.html',
                               categories=categories,
                               items=items,
                               categories_name=categories_name,
                               creator=creator)


# READ - Display all details of a Category Item
# Function available with both Category Item ID and Category Item Name
@app.route('/catalog/<int:categories_id>/<int:categoriesItems_id>/')
def showCategoryItem(categories_id, categoriesItems_id):
    item = session.query(CategoryItems).filter_by(id=categoriesItems_id).one()
    creator = getUserInfo(item.user_id)
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('showPublicCategoryItem.html',
                               item=item,
                               categories_id=categories_id,
                               categoriesItems_id=categoriesItems_id,
                               creator=creator)
    else:
        return render_template('showCategoryItem.html',
                               item=item,
                               categories_id=categories_id,
                               categoriesItems_id=categoriesItems_id,
                               creator=creator)


@app.route('/catalog/<string:categories_name>/<string:categoriesItems_name>/')
def showCategoryItemByName(categories_name, categoriesItems_name):
    item = session.query(CategoryItems).filter_by(
        name=categoriesItems_name).one()
    creator = getUserInfo(item.user_id)
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('showPublicCategoryItem.html',
                               item=item,
                               categories_name=categories_name,
                               categoriesItems_name=categoriesItems_name,
                               creator=creator)
    else:
        return render_template('showCategoryItem.html',
                               item=item,
                               categories_name=categories_name,
                               categoriesItems_name=categoriesItems_name,
                               creator=creator)


# UPDATE - Edit a category Item
# Function available with both category ID and Category Name
@app.route('/catalog/<int:categories_id>/<int:categoriesItems_id>/edit',
           methods=['GET', 'POST'])
def editCategoryItem(categories_id, categoriesItems_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(CategoryItems).filter_by(
        id=categoriesItems_id).one()
    if editedItem.user_id != login_session['user_id']:
        flash("Edit is only available to the owner of the item!")
        return redirect(url_for('showCategory',
                                categories_id=categories_id))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash("Category Item Edited!")
        return redirect(url_for('showCategory',
                                categories_id=categories_id))
    else:
        return render_template('editCategoryItem.html',
                               categories_id=categories_id,
                               categoriesItems_id=categoriesItems_id,
                               item=editedItem)


@app.route('/catalog/<string:categories_name>/'
           '<string:categoriesItems_name>/edit',
           methods=['GET', 'POST'])
def editCategoryItemByName(categories_name, categoriesItems_name):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(CategoryItems).filter_by(
        name=categoriesItems_name).one()
    if editedItem.user_id != login_session['user_id']:
        flash("Edit is only available to the owner of the item!")
        return redirect(url_for('showCategoryByName',
                                categories_name=categories_name))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash("Category Item Edited!")
        return redirect(url_for('showCategoryByName',
                                categories_name=categories_name))
    else:
        return render_template('editCategoryItem.html',
                               categories_name=categories_name,
                               categoriesItems_name=categoriesItems_name,
                               item=editedItem)


# DELETE - Remove a category Item
# Function available with both category ID and Category Name
@app.route('/catalog/<int:categories_id>/<int:categoriesItems_id>/delete',
           methods=['GET', 'POST'])
def deleteCategoryItem(categories_id, categoriesItems_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(CategoryItems).filter_by(
        id=categoriesItems_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        flash("Delete is only available to the owner of the item")
        return redirect(url_for('showCategory',
                                categories_id=categories_id))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Category Item Deleted!")
        return redirect(url_for('showCategory',
                                categories_id=categories_id))
    else:
        return render_template('deleteCategoryItem.html',
                               categories_id=categories_id,
                               categoriesItems_id=categoriesItems_id,
                               itemToDelete=itemToDelete)


@app.route('/catalog/<string:categories_name>/'
           '<string:categoriesItems_name>/delete',
           methods=['GET', 'POST'])
def deleteCategoryItemByName(categories_name, categoriesItems_name):
    if 'username' not in login_session:
        return redirect('/login')
    categoryNameID = session.query(CategoryItems).filter_by(
        name=categoriesItems_name).one()
    categoriesItems_id = categoryNameID.id
    itemToDelete = session.query(CategoryItems).filter_by(
        id=categoriesItems_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        flash("Delete is only available to the owner of the item")
        return redirect(url_for('showCategoryByName',
                                categories_name=categories_name))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Category Item Deleted!")
        return redirect(url_for('showCategoryByName',
                                categories_name=categories_name))
    else:
        return render_template('deleteCategoryItem.html',
                               categories_name=categories_name,
                               categoriesItems_name=categoriesItems_name,
                               itemToDelete=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
