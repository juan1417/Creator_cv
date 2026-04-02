from creator_cv import create_app

app = create_app()


def main():
    print("Hello from creator-cv!")
    print("Run dev server: uv run flask --app creator_cv:create_app run")


if __name__ == "__main__":
    main()
