# Udacity FSND Catalog DB Project

## Description
A web based catalog application that provides a simple setup to store items

Create a category to group items
	Each category contains:
		- name

Create an item within that category
	Each item contains:
		- name
		- description
		- category

Each item within the database is world readable
Each item is owned by a user, who can add/edit/delete those items/categories

## Files
- application.py
- models.py
- readme.md
- client_secrets.json
- fb_client_secrets.json
- static/
- templates/

## Usage
Copy all files to a local directory

*if desired* - sample data can be created by running 'lotsofitems.py'

Run the `application.py` file within a python shell to start the web server

The server will create the catalog.db file to store users & catalog together

Login with Google, Facebook, or local credentials

To clear the DB and start over:
	1. stop the application
	2. delete the catalog.db file

## Links
Web Access: http://localhost:5000/

JSON Access:
Catalog: http://localhost:5000/catalog/JSON
To see specific details of an item, use either ID or Name, as below
ID Number:
Category: http://localhost:5000/catalog/<category ID>/JSON
Catalog Item: http://localhost:5000/catalog/<category ID>/<category ID>/JSON
Name:
Category: http://localhost:5000/catalog/<category name>/JSON
Catalog Item: http://localhost:5000/catalog/<category name>/<category item>/JSON

## Code
This project was possible because of the Udacity Forums and Stack Overflow, without which I would have been lost!

### License
MIT License

### Author
Chris Baines