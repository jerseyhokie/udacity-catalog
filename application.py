from models import Base, Categories, CategoryItems, User
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask import session as login_session
from flask import make_response
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import random
import string
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Catalog Web Interface
#    Establishes all the CRUD operations via webpages
#    Each method is listed in CRUD order, categories then categoryItems respectively
#    All methods that edit the DB are protected

# CREATE - Add a new Category to the Catalog
@app.route('/catalog/new', methods=['GET','POST'])
def newCategory():
    if request.method == 'POST':
        newItem = Categories(name=request.form['name'] )
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
    if 'username' not in login_session:
        return render_template('publicCategories.html', categories=categories)
    else:
        return render_template('categories.html', categories=categories)

# UPDATE - Edit a Category
@app.route('/catalog/<int:categories_id>/edit', methods=['GET','POST'])
def editCategory(categories_id):
    editedItem = session.query(Categories).filter_by(id=categories_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('editCategory.html', categories_id=categories_id, item=editedItem)

# DELETE - Remove a Category
@app.route('/catalog/<int:categories_id>/delete', methods=['GET','POST'])
def deleteCategory(categories_id):
    categoryToDelete = session.query(Categories).filter_by(id=categories_id).one()
    itemsToDelete = session.query(CategoryItems).filter_by(categories_id=categories_id)
    if request.method == 'POST':

        # Insert code to delete items from CategoryItems with categories_id

        for i in itemsToDelete:
            session.delete(i)
        
        session.delete(categoryToDelete)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteCategory.html', itemToDelete=categoryToDelete, items=itemsToDelete,
         categories_id=categories_id)

# CREATE - Add a new Category Item to a specific Category
@app.route('/catalog/<int:categories_id>/new', methods=['GET','POST'])
def newCategoryItem(categories_id):
    if request.method == 'POST':
        newItem = CategoryItems(name=request.form['name'], description=request.form['description'],
            categories_id=categories_id)
        session.add(newItem)
        session.commit()
        flash("New Category Item added!")
        return redirect(url_for('showCategory', categories_id=categories_id))
    else:
        return render_template('newCategoryItem.html', categories_id=categories_id)


# READ - Display all of the items in a single Category
@app.route('/catalog/<int:categories_id>/')
def showCategory(categories_id):
    categories = session.query(Categories).filter_by(id=categories_id).one()
    items = session.query(CategoryItems).filter_by(categories_id=categories_id)
    return render_template('showCategory.html', categories=categories,
        items=items, categories_id=categories_id)


# UPDATE - Edit a category Item
@app.route('/catalog/<int:categories_id>/<int:categoriesItems_id>/edit', methods=['GET','POST'])
def editCategoryItem(categories_id, categoriesItems_id):
    editedItem = session.query(CategoryItems).filter_by(id=categoriesItems_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showCategory', categories_id=categories_id))
    else:
        return render_template(
            'editCategoryItem.html', categories_id=categories_id, categoriesItems_id=categoriesItems_id,
            item=editedItem)


# DELETE - Remove a category Item
@app.route('/catalog/<int:categories_id>/<int:categoriesItems_id>/delete', methods=['GET','POST'])
def deleteCategoryItem(categories_id, categoriesItems_id):
    itemToDelete = session.query(CategoryItems).filter_by(id=categoriesItems_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showCategory', categories_id=categories_id))
    else:
        return render_template('deleteCategoryItem.html', categories_id=categories_id, 
            categoriesItems_id=categoriesItems_id,  itemToDelete=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)