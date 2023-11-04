from colorama import Fore, Back, Style, init
import tkinter as tk
from tkinter import simpledialog

import json
import time
import random
import sys
import os

init(autoreset=True)

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def create_template(template_name, src_area, capsule_width):

    template_data = {
        "class": "line_map",
        "src_area": src_area,
        "variants_y": {
            "highlight": src_area[3] - 20,
            "passed": src_area[3] - 20
        },
        "animations": {
            "highlight": {
                "duration_on": 1,
                "duration_off": 1
            }
        },
        "capsule_width": capsule_width,
        "capsules_x": {}
    }

    with open(f"{template_name}.json", "w") as json_file:
        json.dump(template_data, json_file, indent=4)

def create_new_display():
    display_name = simpledialog.askstring("Create New Display", "Enter display name:")
    if display_name:
        texture = simpledialog.askstring("Create New Display", "Enter texture (filename of the .png for the entire display):")
        texture_width = simpledialog.askinteger("Create New Display", "Enter texture width:")
        texture_height = simpledialog.askinteger("Create New Display", "Enter texture height:")

        left_src_area = simpledialog.askstring("Create New Display", "Enter left doors src area (x start, y start, x end, y end):")
        left_src_area_values = [int(val) for val in left_src_area.split(",")]
        left_src_area_width = left_src_area_values[2] - left_src_area_values[0]
        left_src_area_height = left_src_area_values[3] - left_src_area_values[1]

        leftdoors_capsule_width = simpledialog.askinteger("Create New Display", "Enter capsule width for left doors:")

        right_src_area = simpledialog.askstring("Create New Display", "Enter right doors src area (x start, y start, x end, y end):")
        right_src_area_values = [int(val) for val in right_src_area.split(",")]
        right_src_area_width = right_src_area_values[2] - right_src_area_values[0]
        right_src_area_height = right_src_area_values[3] - right_src_area_values[1]

        rightdoors_capsule_width = simpledialog.askinteger("Create New Display", "Enter capsule width for right doors:")

        left_highlight = left_src_area_values[1] + left_src_area_height // 2
        left_passed = left_highlight

        right_highlight = right_src_area_values[1] + right_src_area_height // 2
        right_passed = right_highlight

        display_data = {
            "version": 1,
            "texture": texture,
            "texture_size": [texture_width, texture_height],
            "templates": {
                "leftdoors": {
                    "class": "include",
                    "source": f"{display_name}_leftdoors.json"
                },
                "rightdoors": {
                    "class": "include",
                    "source": f"{display_name}_rightdoors.json"
                }
            },
            "logic": {
                "class": "sequence",
                "nodes": [
                    {
                        "class": "if",
                        "nodes": []
                    }
                ]
            }
        }

        with open(f"{display_name}.json", "w") as json_file:
            json.dump(display_data, json_file, indent=4)

        create_template(f"{display_name}_leftdoors", left_src_area_values, leftdoors_capsule_width)
        create_template(f"{display_name}_rightdoors", right_src_area_values, rightdoors_capsule_width)
        create_slots_json(display_name, left_src_area_width, left_src_area_height, right_src_area_width, right_src_area_height)

        print("New display created.")

def create_station(display_name, station_name):
    display_filename = f"{display_name}.json"
    try:
        with open(display_filename, "r") as json_file:
            data = json.load(json_file)

            available_routes = sorted([route["when"].replace("$route[0].en == ", "") for route in data["logic"]["nodes"][0]["nodes"] if "when" in route])

            if not available_routes:
                print(f"No routes found in display '{display_name}'. Please create a route first.")
                return

            print("Available routes:")
            for i, route in enumerate(available_routes):
                print(f"{i + 1}. {route}")

            while True:
                route_choice = input("Select a route (1, 2, 3, ...): ")

                if route_choice.isdigit() and 1 <= int(route_choice) <= len(available_routes):
                    selected_route = available_routes[int(route_choice) - 1]
                    break
                else:
                    print("Invalid route choice. Please enter a valid number.")

            leftdoors_capsule_x = int(simpledialog.askstring("Create New Station", f"Enter the capsule_x value for '{station_name}' station in leftdoors:"))

            rightdoors_capsule_x = int(simpledialog.askstring("Create New Station", f"Enter the capsule_x value for '{station_name}' station in rightdoors:"))

            leftdoors_filename = f"{display_name}_leftdoors.json"
            rightdoors_filename = f"{display_name}_rightdoors.json"

            with open(leftdoors_filename, "r") as leftdoors_file:
                leftdoors_data = json.load(leftdoors_file)
                leftdoors_data["capsules_x"][station_name] = leftdoors_capsule_x
            with open(leftdoors_filename, "w") as leftdoors_file:
                json.dump(leftdoors_data, leftdoors_file, indent=4)

            with open(rightdoors_filename, "r") as rightdoors_file:
                rightdoors_data = json.load(rightdoors_file)
                rightdoors_data["capsules_x"][station_name] = rightdoors_capsule_x
            with open(rightdoors_filename, "w") as rightdoors_file:
                json.dump(rightdoors_data, rightdoors_file, indent=4)

            new_station = {
                "when": station_name,
                "then": {
                    "class": "sequence",
                    "nodes": [
                        {
                            "class": "draw_line_map",
                            "template": "leftdoors",
                            "slot": "sl",
                            "target": station_name,
                            "direction": "right",
                            "dst_area": [0, 0, 1, 1]
                        },
                        {
                            "class": "draw_line_map",
                            "template": "rightdoors",
                            "slot": "sr",
                            "target": station_name,
                            "direction": "left",
                            "dst_area": [0, 0, 1, 1]
                        }
                    ]
                }
            }


            route = next((r for r in data["logic"]["nodes"][0]["nodes"] if "when" in r and r["when"] == f"$route[0].en == {selected_route}"), None)

            if route:

                if "then" not in route:
                    route["then"] = {}


                if "nodes" not in route["then"]:
                    route["then"]["nodes"] = []

                route["then"]["nodes"].append(new_station)

                with open(display_filename, "w") as json_file:
                    json.dump(data, json_file, indent=4)

                print(f"New station '{station_name}' created in route '{selected_route}' in display '{display_name}'.")
            else:
                print(f"Route '{selected_route}' not found in display '{display_name}'.")
    except FileNotFoundError:
        print(f"Display '{display_name}' not found.")

def parse_corners_input(input_str):

    corners = []
    try:
        corner_strs = input_str.split("],")
        for corner_str in corner_strs:
            corner_str = corner_str.strip().strip("[]")
            corner_values = [float(val) for val in corner_str.split(",")]
            corners.append(corner_values)
    except Exception:
        return None
    return corners

def list_stations_by_route(display_name, route_name):
    display_filename = f"{display_name}.json"
    
    try:
        with open(display_filename, "r") as json_file:
            data = json.load(json_file)
            stations = None
            for route in data["logic"]["nodes"][0]["nodes"]:
                if "when" in route and route["when"] == f"$route[0].en == {route_name}":
                    stations = route["then"]["nodes"]
                    break

            if stations:
                station_names = [station["when"] for station in stations if "when" in station]
                return station_names
            else:
                return []
    except FileNotFoundError:
        print(f"Display '{display_name}' not found.")
        return []

def create_slots_json(display_name, left_src_area_width, left_src_area_height, right_src_area_width, right_src_area_height):
    num_per_car = simpledialog.askinteger("Create Slots JSON", "Enter how many times the display appears per train car:")

    sr_positions = []
    sl_positions = []
    sr_offsets = []


    sr_position = []
    while True:
        sr_position_values = simpledialog.askstring(
            "Create Slots JSON", f"Enter the coordinates of the four corners for right side display (sr) relative to the display's origin:")
        sr_positions = parse_corners_input(sr_position_values)
        if sr_positions and len(sr_positions) == 4:
            sr_position.append(sr_positions)
            break
        else:
            print("Invalid input. Please enter eight numerical values separated by commas within square brackets.")

    sl_position = []
    while True:
        sl_position_values = simpledialog.askstring(
            "Create Slots JSON", f"Enter the coordinates of the four corners for left side display (sl) relative to the display's origin:")
        sl_positions = parse_corners_input(sl_position_values)
        if sl_positions and len(sl_positions) == 4:
            sl_position.append(sl_positions)
            break
        else:
            print("Invalid input. Please enter eight numerical values separated by commas within square brackets.")


    for _ in range(num_per_car):
        while True:
            sr_offset_values = simpledialog.askstring(
                "Create Slots JSON", f"Enter offset values for the displays (e.g., value1, value2, value3):")
            offset_values = sr_offset_values.split(",")
            if len(offset_values) == 3 and all(val.strip().replace("-", "").replace(".", "", 1).isdigit() for val in offset_values):
                sr_offsets.append([float(val) for val in offset_values])
                break
            else:
                print("Invalid input. Please enter three numerical values separated by commas.")

    sl_positions = [sl_position] * num_per_car


    sr_positions_flat = [item for sublist in sr_positions for item in sublist]
    sl_positions_flat = [item for sublist in sl_positions for item in sublist]

    slots_data = {
        "version": 1,
        "slots": [
            {
                "name": "sr",
                "pos": sr_positions_flat,
                "offsets": sr_offsets
            },
            {
                "name": "sl",
                "pos": sl_positions_flat,
                "offsets": sr_offsets  
            }
        ],
        "slot_groups": {
            "led_door": ["sl", "sr"]
        }
    }

    with open(f"{display_name}_slots.json", "w") as json_file:
        json.dump(slots_data, json_file, indent=4)



def list_stations(display_name):
    display_filename = f"{display_name}.json"
    
    try:
        with open(display_filename, "r") as json_file:
            data = json.load(json_file)
            available_routes = []
            for route in data["logic"]["nodes"][0]["nodes"]:
                if "when" in route:
                    route_name = route["when"].replace("$route[0].en == ", "")
                    available_routes.append(route_name)

            if not available_routes:
                print(f"No routes found in display '{display_name}'. Please create a route first.")
                return

            print("Available routes in the display:")
            for i, route_name in enumerate(available_routes, start=1):
                print(f"{i}. {route_name}")

            while True:
                route_choice = input("Enter the number of the route to list stations for: ")
                if route_choice.isdigit() and 1 <= int(route_choice) <= len(available_routes):
                    selected_route_name = available_routes[int(route_choice) - 1]
                    stations = list_stations_by_route(display_name, selected_route_name)
                    if stations:
                        print(f"Stations in route '{selected_route_name}':")
                        for station in stations:
                            print(f"- {station}")
                    else:
                        print(f"No stations found for route '{selected_route_name}' in display '{display_name}'.")
                    break
                else:
                    print("Invalid route choice. Please select a valid route.")
    except FileNotFoundError:
        print(f"Display '{display_name}' not found.")

def create_route(display_name, route_name):
    display_filename = f"{display_name}.json"
    with open(display_filename, "r") as json_file:
        data = json.load(json_file)

        new_route = {
            "when": f"$route[0].en == {route_name}",
            "then": {
                "class": "switch",
                "target": f"$sta[0].eng",
                "nodes": []
            }
        }
        data["logic"]["nodes"][0]["nodes"].append(new_route)

    with open(display_filename, "w") as json_file:
        json.dump(data, json_file, indent=4)

def edit_main_display():
    display_name = simpledialog.askstring("Edit Main Display", "Enter display name:")
    if display_name:
        display_filename = f"{display_name}.json"
        try:
            with open(display_filename, "r") as json_file:
                data = json.load(json_file)
                

                field_to_edit = simpledialog.askstring("Edit Main Display", "Enter the field to edit (e.g., 'texture', 'texture_size'):")
                
                if field_to_edit in data:
                    new_value = simpledialog.askstring("Edit Main Display", f"Enter the new value for '{field_to_edit}':")
                    data[field_to_edit] = new_value

                    with open(display_filename, "w") as json_file:
                        json.dump(data, json_file, indent=4)
                    
                    print(f"Field '{field_to_edit}' in the main display '{display_name}' edited.")
                else:
                    print(f"Field '{field_to_edit}' not found in the main display '{display_name}'.")
        except FileNotFoundError:
            print(f"Main display '{display_name}' not found.")


def edit_left_doors():
    display_name = simpledialog.askstring("Edit Left Doors", "Enter display name:")
    if display_name:
        leftdoors_filename = f"{display_name}_leftdoors.json"
        try:
            with open(leftdoors_filename, "r") as json_file:
                data = json.load(json_file)

                field_to_edit = simpledialog.askstring("Edit Left Doors", "Enter the field to edit (e.g., 'src_area', 'capsule_width'):")
                
                if field_to_edit in data:
                    new_value = simpledialog.askstring("Edit Left Doors", f"Enter the new value for '{field_to_edit}':")
                    data[field_to_edit] = new_value
                    
                    with open(leftdoors_filename, "w") as json_file:
                        json.dump(data, json_file, indent=4)
                    
                    print(f"Field '{field_to_edit}' in left doors template for '{display_name}' edited.")
                else:
                    print(f"Field '{field_to_edit}' not found in the left doors template for '{display_name}'.")
        except FileNotFoundError:
            print(f"Left doors template for '{display_name}' not found.")

def edit_right_doors():
    display_name = simpledialog.askstring("Edit Right Doors", "Enter display name:")
    if display_name:
        rightdoors_filename = f"{display_name}_rightdoors.json"
        try:
            with open(rightdoors_filename, "r") as json_file:
                data = json.load(json_file)

                field_to_edit = simpledialog.askstring("Edit Right Doors", "Enter the field to edit (e.g., 'src_area', 'capsule_width'):")
                
                if field_to_edit in data:
                    new_value = simpledialog.askstring("Edit Right Doors", f"Enter the new value for '{field_to_edit}':")
                    data[field_to_edit] = new_value
                    
                    with open(rightdoors_filename, "w") as json_file:
                        json.dump(data, json_file, indent=4)
                    
                    print(f"Field '{field_to_edit}' in right doors template for '{display_name}' edited.")
                else:
                    print(f"Field '{field_to_edit}' not found in the right doors template for '{display_name}'.")
        except FileNotFoundError:
            print(f"Right doors template for '{display_name}' not found.")

def edit_slots():
    display_name = simpledialog.askstring("Edit Slots", "Enter display name:")
    if display_name:
        slots_filename = f"{display_name}_slots.json"
        try:
            with open(slots_filename, "r") as json_file:
                data = json.load(json_file)

                field_to_edit = simpledialog.askstring("Edit Slots", "Enter the field to edit (e.g., 'slots', 'slot_groups'):")
                
                if field_to_edit in data:
                    new_value = simpledialog.askstring("Edit Slots", f"Enter the new value for '{field_to_edit}':")
                    data[field_to_edit] = new_value
                    

                    with open(slots_filename, "w") as json_file:
                        json.dump(data, json_file, indent=4)
                    
                    print(f"Field '{field_to_edit}' in slots data for '{display_name}' edited.")
                else:
                    print(f"Field '{field_to_edit}' not found in the slots data for '{display_name}'.")
        except FileNotFoundError:
            print(f"Slots data for '{display_name}' not found.")

def show_title_and_description():
    title = r"""

  _   _  _______  ______         _____  _       _____ 
 | \ | ||__   __||  ____|       / ____|| |     |_   _|
 |  \| |   | |   | |__  ______ | |     | |       | |  
 | . ` |   | |   |  __||______|| |     | |       | |  
 | |\  |   | |   | |____       | |____ | |____  _| |_ 
 |_| \_|   |_|   |______|       \_____||______||_____|
 | |            |  __ \               (_)(_)          
 | |__   _   _  | |  | |  ___    ___   _  _           
 | '_ \ | | | | | |  | | / _ \  / _ \ | || |          
 | |_) || |_| | | |__| || (_) || (_) || || |          
 |_.__/  \__, | |_____/  \___/  \___/ | ||_|          
          __/ |                      _/ |             
         |___/                      |__/              

"""
    description = """
This is a semi-commandline program (GUI popups will appear) to easily create Dynamic Route Displays using Zbx1425's mod, Nemo's Transit Expansion.
"""

    warning = """
🚧 WARNING: This version is pre-alpha and may have missing features and bugs.
🚧 Use it at your own risk!
"""


    glitched_title = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=:;,.<>?[]{}|') if c != '\n' and random.random() < 0.2 else c for c in title)
    
    clear_console()
    print(Fore.CYAN + glitched_title)
    time.sleep(1) 
    clear_console()
    print(Fore.CYAN + glitched_title)


    print(Fore.MAGENTA + description)
    print()


    print(Fore.YELLOW + warning)
    print(Fore.GREEN + "Press 'Enter' to continue...")


    input()


def main():
    root = tk.Tk()
    root.withdraw()  
    show_title_and_description()
    clear_console()
    print(Fore.YELLOW + "\n🚧 Please note that if you use an existing display, filenames should be named a certain way for now.")
    print(Fore.GREEN + "\nMain Display File: displayname.json")
    print(Fore.GREEN + "\nLeft side: displayname_leftdoors.json")
    print(Fore.GREEN + "\nRight side: displayname_rightdoors.json")
    print(Fore.GREEN + "\nSlots: displayname_slots.json")
    print("\n ")
    print(Fore.CYAN + "\n🚧 Displays created by this program already meet this requirement. A way to change each file will be added soon.")
    print("\n ")
    display_name = input("[Optional] Enter the display name: ")

    while True:
        clear_console() 
        print("\nSelected Display: " + display_name)
        print("\n ")
        print("\nOptions:")
        print("1. Create a new display")
        print("2. Create a station")
        print("3. Create a route")
        print("4. List stations in a route")
        print("5. Advanced")
        print("6. Change Display Name")
        print("7. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            create_new_display()
        elif choice == "2":
            station_name = input("Enter the station name: ")
            create_station(display_name, station_name)
        elif choice == "3":
            route_name = input("Enter the route name: ")
            create_route(display_name, route_name)
        elif choice == "4":
            list_stations(display_name)
        elif choice == "5":
            advanced_choice = input("Advanced Options:\n1. Edit Main Display\n2. Edit Left Doors\n3. Edit Right Doors\n4. Edit Slots\n5. Back\nEnter your choice: ")
            if advanced_choice == "1":
                edit_main_display()
            elif advanced_choice == "2":
                edit_left_doors()
            elif advanced_choice == "3":
                edit_right_doors()
            elif advanced_choice == "4":
                edit_slots()
            elif advanced_choice == "5":
                continue
            else:
                print("Invalid choice.")
        elif choice == "6":
            display_name = input("Enter the new display name: ")
        elif choice == "7":
            break
        else:
            print("Invalid choice. Please try again.")

        input("Press Enter to continue...")

if __name__ == "__main__":
    main()