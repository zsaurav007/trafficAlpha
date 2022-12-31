from application import create_app, create_users

app = create_app()
app.app_context().push()
create_users()   # add initial users

if __name__ == '__main__':
    app.run(debug=True)
