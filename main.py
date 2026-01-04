from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)





@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/signup')
def signup():
    return  render_template("signup.html")

@app.route('/login-admin')
def login_admin():
    return render_template("login_admin.html")
@app.route('/')
def main():
    return render_template("homepage.html")

if __name__ == '__main__':
    app.run(debug=True)