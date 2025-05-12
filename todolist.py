import json
from datetime import date
import re

def get_todo():
    try:
        with open('todo.json', 'r') as file:
            content = file.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_todo(data):
    with open("todo.json", "w") as file:
        json.dump(data, file, indent=4)

def add_todo(task):
    data = get_todo()
    
    data.append({"S.No":len(data)+1,"task": task,"date":str(date.today()), "completed": False})

    save_todo(data)
    return "task added successfully"


def marked_done(task="", SNO=0):
    data = get_todo()
    updated = False

    if task != "":
        for i in data:
            if i["task"] == task:
                i["completed"] = True
                updated = True
                break
    elif SNO >0:
        for i in data:
            if i["S.No"] == SNO:
                i["completed"] = True
                updated = True
                break

    if updated:
        save_todo(data)
        return True,"Task marked done"
    else:
        return False ,"Task not found"


def get_not_comp():
    data = get_todo()
    not_comp = []
    for i in data:
        if i["completed"] == False:
            not_comp.append(i)
    return not_comp

import re

def extract_task(command):
    match = re.search(r"(?:add|mark(?:ed)?)\s+(.*?)\s*(?:to[- ]do|done|task done)?$", command, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def extract_task_no(command):
    match = re.search(r"(?:no|number)[\s:]*([0-9]+)", command, re.IGNORECASE)
    if match:
        return int(match.group(1).strip())
    return None

def intent_detection(command):
    intents= {
        "add": ["add"],
        "mark": ["mark","mark done","done","task done","completed"],
        "show": ["show todo","show tasks"],
        "showall":["show all task","show all todo"]
    }
    for intent,keys in intents.items():
        for key in keys:
            key=key.replace(" ","")
            if key in command.replace(" ",""):
                return intent

def org_todo(todo_list):
    if not todo_list:
        return ""
    todo = "to-do list:\nS.No\tTask\tDate\tCompleted\n"
    for i in todo_list:
        todo += f"{i['S.No']}\t{i['task']}\t{i['date']}\t{str(i['completed'])}\n"
    return todo


def process_todo_cmd(cmd):
    intent = intent_detection(cmd)
    message = ""
    todo = None
    if intent == "add":
        task = extract_task(cmd)
        message = add_todo(task)
    elif intent == "mark":
        task = extract_task(cmd)
        task_no = extract_task_no(cmd)
        flag,message = marked_done(task)
        if not flag: 
            flag,message = marked_done(SNO=task_no)
    elif intent == "show":
        todo = get_not_comp()
        if todo == []:
            message = "No tasks to show"
        else :
            message = "to-do list are:"
    elif intent == "showall":
        todo = get_todo()
        if todo == []:
            message = "No tasks to show"
        else:
            message = "to-do list are:"
    else:
        message = "cann't understand the command"
    return message,org_todo(todo) 


process_todo_cmd("mark taks no 2 done")