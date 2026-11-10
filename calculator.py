import tkinter as tk
from tkinter import messagebox, simpledialog
import math
import ast
import operator
import statistics
import re

# ================= COLORS =================

BG = "#101B2D"
DISPLAY_BG = "#18283D"
BUTTON_BG = "#30445C"
SPECIAL_BG = "#52677F"
GOLD = "#38A9E8"
DARK_GOLD = "#1688D4"
WHITE = "#FFFFFF"
MUTED = "#9CB3CC"

# ================= WINDOW =================

root = tk.Tk()
root.title("Scientific Calculator")
root.geometry("400x580")
root.minsize(370, 540)
root.configure(bg=BG)

expression = ""
degree_mode = True
power_pending = False
history_items = []
variable_values = {}

# ================= SAFE CALCULATOR =================

def safe_eval(expr):
    functions = {
        "sin": lambda x: math.sin(math.radians(x) if degree_mode else x),
        "cos": lambda x: math.cos(math.radians(x) if degree_mode else x),
        "tan": lambda x: math.tan(math.radians(x) if degree_mode else x),
        "sqrt": math.sqrt,
        "log": math.log10,
        "ln": math.log,
        "factorial": math.factorial,
        "abs": abs
    }

    names = {"pi": math.pi, "e": math.e}

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod
    }

    unary = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg
    }

    def calculate_node(node):
        if isinstance(node, ast.Expression):
            return calculate_node(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Invalid number")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)

            if op_type not in operators:
                raise ValueError("Invalid operator")

            left = calculate_node(node.left)
            right = calculate_node(node.right)

            if op_type == ast.Pow and abs(right) > 100:
                raise ValueError("Power is too large")

            return operators[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)

            if op_type not in unary:
                raise ValueError("Invalid operation")

            return unary[op_type](calculate_node(node.operand))

        if isinstance(node, ast.Name):
            if node.id in names:
                return names[node.id]

            raise ValueError("Unknown value")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Invalid function")

            name = node.func.id

            if name not in functions:
                raise ValueError("Invalid function")

            args = [calculate_node(arg) for arg in node.args]

            if len(args) != 1:
                raise ValueError("One argument required")

            return functions[name](args[0])

        raise ValueError("Invalid expression")

    return calculate_node(ast.parse(expr, mode="eval"))


# ================= DISPLAY FUNCTIONS =================

def update_display():
    display.config(text=expression if expression else "0")


def press(value):
    global expression

    if expression == "Error":
        expression = ""

    value = str(value)

    if value in ("pi", "e") and expression and (
        expression[-1].isdigit()
        or expression.endswith(")")
        or expression.endswith("pi")
        or expression.endswith("e")
    ):
        expression += "*"

    expression += value
    update_display()


def clear_all():
    global expression, power_pending

    expression = ""
    power_pending = False
    expression_label.config(text="")
    update_display()


def clear_current():
    global expression

    if not expression or expression == "Error":
        clear_all()
        return

    if expression.endswith(")"):
        depth = 0
        start = None

        for i in range(len(expression) - 1, -1, -1):
            if expression[i] == ")":
                depth += 1

            elif expression[i] == "(":
                depth -= 1

                if depth == 0:
                    start = i
                    break

        if start is not None:
            while start > 0 and expression[start - 1].isalpha():
                start -= 1

            expression = expression[:start]

        else:
            expression = expression[:-1]

    else:
        match = re.search(
            r"(?:\d+(?:\.\d*)?|\.\d+|pi|e)$",
            expression
        )

        if match:
            expression = expression[:match.start()]

        elif expression:
            expression = expression[:-1]

    update_display()


def backspace():
    global expression

    if expression == "Error":
        expression = ""
    else:
        expression = expression[:-1]

    update_display()


def apply_percent():
    global expression

    if not expression or expression == "Error":
        return

    if expression.endswith(")"):
        depth = 0
        start = None

        for i in range(len(expression) - 1, -1, -1):
            if expression[i] == ")":
                depth += 1

            elif expression[i] == "(":
                depth -= 1

                if depth == 0:
                    start = i
                    break

        if start is None:
            return

        while start > 0 and expression[start - 1].isalpha():
            start -= 1

        token_start = start

    else:
        match = re.search(
            r"(?:\d+(?:\.\d*)?|\.\d+|pi|e)$",
            expression
        )

        if not match:
            return

        token_start = match.start()

    value = expression[token_start:]

    expression = (
        expression[:token_start]
        + "(" + value + "/100)"
    )

    update_display()


# ================= HISTORY =================

def add_history(item):
    history_items.append(item)


def show_history():
    history_window = tk.Toplevel(root)
    history_window.title("Calculation History")
    history_window.geometry("350x400")
    history_window.configure(bg=BG)

    tk.Label(
        history_window,
        text="Calculation History",
        bg=BG,
        fg=GOLD,
        font=("Segoe UI", 16, "bold")
    ).pack(pady=12)

    history_list = tk.Listbox(
        history_window,
        bg=DISPLAY_BG,
        fg=WHITE,
        font=("Segoe UI", 11),
        selectbackground=GOLD,
        relief="flat"
    )

    history_list.pack(
        fill="both",
        expand=True,
        padx=12,
        pady=10
    )

    if history_items:
        for item in reversed(history_items):
            history_list.insert("end", item)

    else:
        history_list.insert("end", "No calculation history yet.")

    tk.Button(
        history_window,
        text="CLEAR HISTORY",
        bg=GOLD,
        fg="#171717",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        command=lambda: clear_history(history_list)
    ).pack(fill="x", padx=12, pady=10)


def clear_history(history_list):
    history_items.clear()
    history_list.delete(0, "end")
    history_list.insert("end", "No calculation history yet.")


# ================= CALCULATION =================

def calculate():
    global expression, power_pending

    if not expression or expression == "Error":
        return

    try:
        original = expression
        result = safe_eval(expression)

        if isinstance(result, float):
            if not math.isfinite(result):
                raise ValueError("Invalid result")

            if result.is_integer():
                result = int(result)
            else:
                result = round(result, 10)

        expression_label.config(text=original + " =")

        expression = str(result)
        power_pending = False

        update_display()
        add_history(original + " = " + str(result))

    except Exception as error:
        expression = "Error"
        power_pending = False
        update_display()
        messagebox.showerror("Calculation Error", str(error))


# ================= SCIENTIFIC FUNCTIONS =================

def set_angle_mode(mode):
    global degree_mode

    degree_mode = (mode == "DEG")

    deg_button.config(
        bg=GOLD if degree_mode else BUTTON_BG
    )

    rad_button.config(
        bg=GOLD if not degree_mode else BUTTON_BG
    )


def scientific_action(value):
    global expression, power_pending

    if value == "AC":
        clear_all()

    elif value == "C":
        clear_current()

    elif value == "DEL":
        backspace()

    elif value == "=":
        calculate()

    elif value == "DEG":
        set_angle_mode("DEG")

    elif value == "RAD":
        set_angle_mode("RAD")

    elif value == "π":
        press("pi")

    elif value == "e":
        press("e")

    elif value == "xʸ":
        if expression and expression != "Error":
            expression += "**"
            power_pending = True
            update_display()

    elif value == "%":
        apply_percent()

    elif value == "÷":
        press("/")

    elif value == "×":
        press("*")

    elif value == "−":
        press("-")

    elif value in [
        "√", "x²", "x³", "1/x",
        "n!", "sin", "cos", "tan", "log", "ln"
    ]:

        if not expression or expression == "Error":
            return

        current = expression

        if value == "√":
            expression = "sqrt(" + current + ")"

        elif value == "x²":
            expression = "(" + current + ")**2"

        elif value == "x³":
            expression = "(" + current + ")**3"

        elif value == "1/x":
            expression = "1/(" + current + ")"

        elif value == "n!":
            expression = "factorial(" + current + ")"

        else:
            expression = value + "(" + current + ")"

        calculate()

    else:
        press(value)


# ================= BUTTON DESIGN =================

def create_button(
    parent,
    text,
    command,
    color=BUTTON_BG,
    row=0,
    column=0,
    colspan=1,
    font_size=12
):

    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg=WHITE,
        activebackground=GOLD,
        activeforeground=WHITE,
        font=("Segoe UI", font_size, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2"
    )

    btn.grid(
        row=row,
        column=column,
        columnspan=colspan,
        sticky="nsew",
        padx=3,
        pady=3,
        ipady=9
    )

    return btn


# ================= MAIN LAYOUT =================

mode_frame = tk.Frame(root, bg=BG)
mode_frame.pack(fill="x", padx=10, pady=10)

display_frame = tk.Frame(root, bg=DISPLAY_BG)
display_frame.pack(fill="x", padx=10, pady=5)

expression_label = tk.Label(
    display_frame,
    text="",
    bg=DISPLAY_BG,
    fg=MUTED,
    font=("Segoe UI", 10),
    anchor="e"
)

expression_label.pack(fill="x", padx=15, pady=(8, 0))

display = tk.Label(
    display_frame,
    text="0",
    bg=DISPLAY_BG,
    fg=GOLD,
    font=("Segoe UI", 27, "bold"),
    anchor="e"
)

display.pack(fill="x", padx=15, pady=(4, 14))

content_frame = tk.Frame(root, bg=BG)
content_frame.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=5
)

basic_frame = tk.Frame(content_frame, bg=BG)
advanced_frame = tk.Frame(content_frame, bg=BG)
stats_frame = tk.Frame(content_frame, bg=BG)


# ================= BASIC KEYPAD =================

basic_keys = [
    ["(", ")", "%", "DEL"],
    ["7", "8", "9", "÷"],
    ["4", "5", "6", "×"],
    ["1", "2", "3", "−"],
    ["0", ".", "C", "+"],
    ["="]
]

for i, row in enumerate(basic_keys):

    basic_frame.grid_rowconfigure(i, weight=1)

    for j, key in enumerate(row):

        color = BUTTON_BG

        if key in ["÷", "×", "−", "+"]:
            color = GOLD

        elif key == "=":
            color = DARK_GOLD

        elif key in ["C", "DEL", "%"]:
            color = SPECIAL_BG

        if key == "=":

            create_button(
                basic_frame,
                key,
                calculate,
                color,
                row=i,
                column=0,
                colspan=4,
                font_size=14
            )

        else:

            commands = {
                "C": clear_current,
                "DEL": backspace,
                "%": apply_percent,
                "÷": lambda: press("/"),
                "×": lambda: press("*"),
                "−": lambda: press("-")
            }

            command = commands.get(
                key,
                lambda k=key: press(k)
            )

            create_button(
                basic_frame,
                key,
                command,
                color,
                row=i,
                column=j
            )

for j in range(4):
    basic_frame.grid_columnconfigure(j, weight=1)


# ================= ADVANCED KEYPAD =================

angle_frame = tk.Frame(advanced_frame, bg=BG)

angle_frame.grid(
    row=0,
    column=0,
    columnspan=5,
    sticky="ew",
    padx=3,
    pady=4
)

for j in range(2):
    angle_frame.grid_columnconfigure(j, weight=1)


deg_button = tk.Button(
    angle_frame,
    text="DEG",
    command=lambda: set_angle_mode("DEG"),
    bg=GOLD,
    fg="#171717",
    activebackground=DARK_GOLD,
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    cursor="hand2"
)

deg_button.grid(
    row=0,
    column=0,
    sticky="ew",
    padx=3,
    ipady=6
)


rad_button = tk.Button(
    angle_frame,
    text="RAD",
    command=lambda: set_angle_mode("RAD"),
    bg=BUTTON_BG,
    fg=WHITE,
    activebackground=DARK_GOLD,
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    cursor="hand2"
)

rad_button.grid(
    row=0,
    column=1,
    sticky="ew",
    padx=3,
    ipady=6
)


advanced_keys = [
    ["sin", "cos", "tan", "log", "ln"],
    ["√", "x²", "xʸ", "π", "e"],
    ["(", ")", "1/x", "n!", "%"],
    ["7", "8", "9", "÷", "DEL"],
    ["4", "5", "6", "×", "C"],
    ["1", "2", "3", "−", "AC"]
]

for i, row in enumerate(advanced_keys):

    advanced_frame.grid_rowconfigure(i + 1, weight=1)

    for j, key in enumerate(row):

        color = BUTTON_BG

        if key in ["÷", "×", "−"]:
            color = GOLD

        elif key == "=":
            color = DARK_GOLD

        elif key in ["C", "DEL", "AC", "%"]:
            color = SPECIAL_BG

        elif key in [
           "sin", "cos", "tan", "log", "ln",
           "√", "x²", "xʸ", "π", "e", "n!"
]:
         color = "#52677F"

        create_button(
            advanced_frame,
            key,
            lambda k=key: scientific_action(k),
            color,
            row=i + 1,
            column=j,
            font_size=10
        )


# Bottom row

create_button(
    advanced_frame,
    "0",
    lambda: press("0"),
    BUTTON_BG,
    row=7,
    column=0,
    colspan=2,
    font_size=10
)

create_button(
    advanced_frame,
    ".",
    lambda: press("."),
    BUTTON_BG,
    row=7,
    column=2,
    font_size=10
)

create_button(
    advanced_frame,
    "=",
    calculate,
    DARK_GOLD,
    row=7,
    column=3,
    colspan=2,
    font_size=10
)

for j in range(5):
    advanced_frame.grid_columnconfigure(j, weight=1)


# ================= STATISTICS MODE =================

tk.Label(
    stats_frame,
    text="Statistics Calculator",
    bg=BG,
    fg=GOLD,
    font=("Segoe UI", 16, "bold")
).pack(anchor="w", pady=(12, 8))


tk.Label(
    stats_frame,
    text="Enter numbers separated by commas",
    bg=BG,
    fg=MUTED,
    font=("Segoe UI", 10)
).pack(anchor="w")


stats_entry = tk.Entry(
    stats_frame,
    bg=DISPLAY_BG,
    fg=WHITE,
    insertbackground=GOLD,
    font=("Segoe UI", 13),
    relief="flat"
)

stats_entry.pack(fill="x", pady=12, ipady=12)


def calculate_statistics():

    try:
        input_text = stats_entry.get().strip()

        if not input_text:
            raise ValueError("Please enter numbers.")

        values = [
            float(x.strip())
            for x in input_text.split(",")
            if x.strip()
        ]

        if not values:
            raise ValueError("Please enter valid numbers.")

        if not all(math.isfinite(x) for x in values):
            raise ValueError("Please enter finite numbers only.")

        result = {
            "Count": len(values),
            "Sum": sum(values),
            "Mean": statistics.mean(values),
            "Median": statistics.median(values),
            "Mode": statistics.multimode(values),
            "Minimum": min(values),
            "Maximum": max(values),
            "Population Variance": statistics.pvariance(values),
            "Population Std Dev": statistics.pstdev(values)
        }

        if len(values) >= 2:
            result["Sample Variance"] = statistics.variance(values)
            result["Sample Std Dev"] = statistics.stdev(values)

        stats_result.config(state="normal")
        stats_result.delete("1.0", "end")

        for name, value in result.items():
            stats_result.insert(
                "end",
                f"{name}: {value}\n\n"
            )

        stats_result.config(state="disabled")

        add_history("Statistics calculated: " + str(values))

    except ValueError as error:
        messagebox.showerror("Input Error", str(error))

    except Exception as error:
        messagebox.showerror("Error", str(error))


# Calculate button FIRST

stats_calculate_button = tk.Button(
    stats_frame,
    text="CALCULATE STATISTICS",
    command=calculate_statistics,
    bg=GOLD,
    fg=WHITE,
    activebackground=DARK_GOLD,
    activeforeground=WHITE,
    font=("Segoe UI", 11, "bold"),
    relief="flat",
    cursor="hand2"
)

stats_calculate_button.pack(
    pady=5,
    ipadx=12,
    ipady=4
)


# Result box AFTER button

stats_result = tk.Text(
    stats_frame,
    height=8,
    bg=DISPLAY_BG,
    fg=WHITE,
    font=("Segoe UI", 10),
    relief="flat",
    state="disabled"
)

stats_result.pack(
    fill="both",
    expand=True,
    pady=8
)


# ================= MODE SWITCHING =================

def show_mode(mode):

    basic_frame.pack_forget()
    advanced_frame.pack_forget()
    stats_frame.pack_forget()

    if mode == "Statistics":
        display_frame.pack_forget()
        stats_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

    else:
        stats_frame.pack_forget()

        if not display_frame.winfo_manager():
            display_frame.pack(
                fill="x",
                padx=10,
                pady=5,
                before=content_frame
            )

        if mode == "Basic":
            basic_frame.pack(fill="both", expand=True)

        elif mode == "Advanced":
            advanced_frame.pack(fill="both", expand=True)

    for name, btn in mode_buttons.items():
        btn.config(
            bg=GOLD if name == mode else BUTTON_BG,
            fg="#171717" if name == mode else WHITE
        )


# ================= MODE BUTTONS =================

mode_buttons = {}

for mode in ["History", "Basic", "Advanced", "Statistics"]:

    if mode == "History":
        command = show_history
    else:
        command = lambda m=mode: show_mode(m)

    btn = tk.Button(
        mode_frame,
        text=mode,
        command=command,
        bg=GOLD if mode == "Basic" else BUTTON_BG,
        fg="#171717" if mode == "Basic" else WHITE,
        activebackground=GOLD,
        activeforeground="#171717",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        cursor="hand2"
    )

    btn.pack(
        side="left",
        expand=True,
        fill="both",
        padx=3,
        ipady=9
    )

    mode_buttons[mode] = btn


# ================= KEYBOARD SUPPORT =================

def keyboard_input(event):

    # Allow normal typing inside Statistics input box
    if root.focus_get() == stats_entry:
        return

    key = event.keysym
    char = event.char

    # Numbers and decimal point
    if char and char in "0123456789.":
        press(char)

    elif char and char.isalpha():
        press(char.lower())

    # Mathematical operators
    elif char and char in "+-*/()":
        press(char)

    elif char == "%":
        apply_percent()

    # Enter key
    elif key in ("Return", "KP_Enter"):
        calculate()

    # Backspace key
    elif key == "BackSpace":
        backspace()

    # Escape key
    elif key == "Escape":
        clear_all()

    # Numeric keypad operators
    elif key == "KP_Add":
        press("+")
    elif key == "KP_Subtract":
        press("-")
    elif key == "KP_Multiply":
        press("*")
    elif key == "KP_Divide":
        press("/")
    elif key == "KP_Decimal":
        press(".")

    else:
        return

    return "break"


# Enable keyboard support
root.bind_all("<Key>", keyboard_input)
root.focus_force()

show_mode("Basic")
update_display()

root.mainloop()