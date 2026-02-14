from db import init_db
from seed import seed_demo_if_needed
from ui import App

def main():
    init_db()
    seed_demo_if_needed()
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
