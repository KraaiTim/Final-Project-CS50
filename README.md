# TK Restauarant Final Project CS50

## Project Description

This is a restaurant web application that can be used to manage the orders at a restaurant. Customers can access the website by scanning a QR code on their table. This QR code will include the table number in the url and set the table number for the customer. After this, the customer will be redirect to the menu where they can select products before placing their order.
Restaurant employees can, after logging in with their firstname and password, see all the tables and select a table to add products to the order. Employees can register other employees, add and remove tables and add and remove products to the menu.

#### Video Demo: <https://youtu.be/_VwMaBGBUyM>

## Technologies used

The web application build in Python using Flask, SQLite for the local database, SQLAlchemy for quering the database and Marshmallow for serializing the database objects.

## Files

- app.py contains all the SQLAlchemy objects, Marshmallow schemas and Flask routes. First the SQLAlchemy objects are created to create the schema of the database. There is an Employee table, a Product table, a Table table, an Orderline table and an Order table. All these tables are linked via Foreign keys. With the SQLalchemy objects, the Marshmallow Schemas are created. Two schemas are created: One for a single objects and another schema for multiple of the same object. These Marshmallow schemas are used to serialize the SQLalchemy objects before they are passed to the client.
- helpers.py contains all the decorater functions.
- requirements.txt contains all the python packages used.
- restaurant.db is the sqlite database.
- index.html page is the main page that displays the menu and if a table is selected, products can be added to an order. When no table is selected, it will only display the menu.
- 404.html is a standard error page.
- layout.html is the base layout template file that is extended in the other html pages using Jinja.
- login.html is for the login page.
- order.html is to show the overview of the current items on the order. If there are no product on the order, it will display nothing.
- payment_sucessful.html is to show after an order has been sucessfully paid.
- products.html is to show the list of products and the form to add new products to the menu.
- register.html is to register a new employee.
- table_overview.html is a page where the customer can select if the want to order more or see the order overview.
- tables.html is to show the tables and have the possibility to select or remove a table. Tables can also be added via the form on this page.

In the static folder is the minimal css of this project as Bootstrap is used as the CSS framework to style the pages. No JavaScript is used in this project.

## Login

It is possible to log in to the app as an employee. After login the employee id will be stored in a Flask session. The routes only for employees (registration of a new employee, adding of tables and products) are protected with a decorater function that will redirect to the login page if there is no employee id in the Flask session.

On the index page, the customer or the employee can select products which are placed in a cart which is a dictionary stored in the Flask session. After "Add to order" is pressed, an order is created and the products are added to the order in the database. New products can be added to the order later. After the order is complete, the order can be paid which will change the status of the order to "Paid" and redirect the to a succes screen.

## Setup project on Windows

Clone the project from Github or download the full project. In the terminal run the following commands:

    1. pip install virtualenv
    2. python -m venv venv
    3. venv\Scripts\activate
    4. pip install -r requirements.txt
    5. flask drop_db #Drop database if exist
    6. flask create_db #Create new database
    7. flask seed_db #Seed database with test objects
    8. python app.py #Run Flask server

## Use the application like a customer

1. Open http://127.0.0.1:5000/table/1
2. Add products to the cart
3. Click place order
4. Pay the order

## Use the application like an employee

1. Open http://127.0.0.1:5000/login
2. Login with first name "admin" and password "admin"
3. Select a table
4. Add products to the order for the selected table
5. Place the order
6. Click pay order once the customer has paid.
