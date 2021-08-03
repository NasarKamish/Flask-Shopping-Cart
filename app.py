import hmac
import sqlite3
import datetime
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS

db = "TEST.db"


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_users():
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


def init_user_table():
    conn = sqlite3.connect(db)
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


def init_history_table():
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS History (history_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "day TEXT NOT NULL,"
                     "total TEXT NOT NULL,"
                     "date_created TEXT NOT NULL,"
                     "user_id INTEGER NOT NULL,"
                     "FOREIGN KEY (user_id) REFERENCES user (user_id))")
    print("History table created successfully.")


def init_product_table():
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS Product (product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "name TEXT NOT NULL,"
                     "price TEXT NOT NULL"
                     ")")
    print("Product table created successfully.")


def init_items_table():
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS Items (items_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "quantity TEXT NOT NULL,"
                     "date_created TEXT NOT NULL,"
                     "history_id INTEGER NOT NULL,"
                     "product_id INTEGER NOT NULL,"
                     "FOREIGN KEY (history_id) REFERENCES History (history_id),"
                     "FOREIGN KEY (product_id) REFERENCES Product (product_id))"
                     )
    print("Item table created successfully.")


init_user_table()
init_history_table()
init_product_table()
init_items_table()
users = fetch_users()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
CORS(app)

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect(db) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "username,"
                           "password) VALUES(?, ?, ?, ?)", (first_name, last_name, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201
    return response


@app.route('/create-product/', methods=["POST"])
@jwt_required()
def create_product():
    response = {}

    if request.method == "POST":
        product_name = request.form['product_name']
        product_price = request.form['product_price']
        # date_created = datetime.datetime.now()

        with sqlite3.connect(db) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Product ("
                           "name,"
                           "price,"
                           ") VALUES(?, ?)", (product_name, product_price))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "Product added successfully"
        return response


@app.route('/get-products/', methods=["GET"])
def get_products():
    response = {}
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Product")

        products = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = products
    return response


@app.route("/delete-product/<int:product_id>")
@jwt_required()
def delete_post(product_id):
    response = {}
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Product WHERE id=" + str(product_id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "blog post deleted successfully."
    return response


@app.route('/edit-product/<int:product_id>/', methods=["PUT"])
@jwt_required()
def edit_post(product_id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect(db) as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("name") is not None:
                put_data["name"] = incoming_data.get("name")
                with sqlite3.connect(db) as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE product SET name =? WHERE id=?", (put_data["name"], product_id))
                    conn.commit()
                    response['message'] = "Update was successfully"
                    response['status_code'] = 200
            if incoming_data.get("price") is not None:
                put_data['price'] = incoming_data.get('price')

                with sqlite3.connect(db) as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE product SET price =? WHERE id=?", (put_data["price"], product_id))
                    conn.commit()

                    response["content"] = "Content updated successfully"
                    response["status_code"] = 200
    return response


@app.route('/get-product/<int:product_id>/', methods=["GET"])
def get_post(product_id):
    response = {}

    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Product WHERE id=" + str(product_id))

        response["status_code"] = 200
        response["description"] = "Product retrieved successfully"
        response["data"] = cursor.fetchone()

    return jsonify(response)


if __name__ == "__main__":
    app.run()
