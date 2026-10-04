import tkinter as tk
from gui import MazeApp


def main():
    root = tk.Tk()
    app = MazeApp(root)
    app.start_with_default()  # show the required solvable 5×5 maze at launch
    root.mainloop()


if __name__ == "__main__":
    main()
