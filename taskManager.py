#!/usr/bin/env python3
# Created by Ber1y to pratique my python skills: POO, Tkinter, json and logique programming

import os
import json
import logging
import tkinter
from tkinter import *
from tkinter import messagebox

CURRENT_DIRECTORY = os.path.dirname(__file__)
WORKING_DIRECTORY = os.path.join(CURRENT_DIRECTORY, "data")
DATA_FILE = None

def initialData():
	global DATA_FILE
	DATA_FILE = os.path.join(WORKING_DIRECTORY, "settings.json")
	if not os.path.exists(WORKING_DIRECTORY):
		os.makedirs(WORKING_DIRECTORY)
		with open(DATA_FILE, "w") as f:
			json.dump(list(), f, indent=4)

# LOGS = os.path.join(CURRENT_DIRECTORY, WORKING_DIRECTORY, "access.log")
# logging.basicConfig(
#     level = logging.DEBUG, 
#     filename = LOGS, 
#     filemode = 'w', 
#     format = '%(asctime)s - %(levelname)s: %(message)s'
# )

class API:
	def __init__(self, title = ""):
		self.title = title.title()
		initialData()
	
	def __str__(self):
		return self.title

	def _get_element(self):
		with open(DATA_FILE, "r") as f:
			return json.load(f)

	def _write_element(self, content):
		with open(DATA_FILE, "w") as f:
			json.dump(content, f, indent = 4)
	
	def add_to_element(self):
		global DATA_FILE
		all_elements = self._get_element()
		if self.title not in all_elements:
			all_elements.append(self.title)
			self._write_element(all_elements)
			return True
		else:
			# logging.warning(f"L'element '{self.title}' est deja presente dans la liste.")
			return False

	def remove_to_element(self):
		all_elements = self._get_element()
		if self.title in all_elements:
			all_elements.remove(self.title)
			self._write_element(all_elements)

def GetElement():
	initialData()
	with open(DATA_FILE, "r") as f:
		fullData = json.load(f)
	for mindata in fullData:
		return API(mindata)
	

class App(Tk):
	def __init__(self):
		Tk.__init__(self)
		# global call
		self.fullData = GetElement()
		self.api = None

		self.title("Task Manager").title()
		self.resizable(width = False, height = False)
		self.geometry("320x270")

		self.var_entry = StringVar()
		self.entry = Entry(self, textvariable = self.var_entry)
		self.entry.pack(fill = X)

		self.btn = Button(self, text = "Ajouter un element", command = self.add_item)
		self.btn.pack(fill = X)

		self.var_lstb = StringVar()
		self.lstb = Listbox(self, listvariable = self.var_lstb, selectmode = tkinter.MULTIPLE)
		self.lstb.pack(fill = X)
		
		self.load_template()

		self.btn_delete = Button(self, text = "Supprimer le(s) element(s)", command = self.remove_items)
		self.btn_delete.pack(fill = X, side = BOTTOM)

		self.mainloop()
	
	def load_template(self):
		with open(DATA_FILE, "r") as f:
			indices = json.load(f)
			for key, value in enumerate(indices):
				self.lstb.insert(key, value)

	def add_item(self):
		if not self.var_entry.get() or len(self.var_entry.get()) > 25:
			# logging.warning("Attention ! l'element que vous avez entrer est vide.")
			messagebox.showerror("Attention !", "Quelque chose c'est mal passer l'application n'a pas pu effectuer votre action.")
		else:
			# Call the API class with element name on args
			self.api = API(self.var_entry.get())
			if self.api.add_to_element():
				self.api.add_to_element()
				self.lstb.insert(tkinter.END, self.var_entry.get().title())
				self.var_entry.set("")
			else:
				messagebox.showinfo("Info !", "L'element existe deja dans la liste.")

	def remove_items(self):
		with open(DATA_FILE, "r") as f:
			content = json.load(f)

			indices = self.lstb.curselection()
			for deleted in indices:
				if 0 <= deleted < len(content):
					del content[deleted]
				self.lstb.delete(deleted)

		with open(DATA_FILE, "w") as f:
			json.dump(content, f, indent = 4)
if __name__ == '__main__':
	app = App()
	logging.debug("Le programme a bien ete executer.")

