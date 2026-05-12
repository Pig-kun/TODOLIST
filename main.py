from views import MainWindow
from controllers import AppController


def main():
    view = MainWindow()
    AppController(view)
    view.run()


if __name__ == "__main__":
    main()
