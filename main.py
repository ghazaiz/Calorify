from app import create_app, initialize_database


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run()