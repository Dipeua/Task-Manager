#!/usr/bin/env python3
# Created by Ber1y to pratique my python skills: POO, Tkinter, json and logique programming

# Importation des modules nécessaires
import os
import json
import logging
import tkinter
from tkinter import *
from tkinter import messagebox

# Définition des répertoires et du fichier de données
CURRENT_DIRECTORY = os.path.dirname(__file__)
WORKING_DIRECTORY = os.path.join(CURRENT_DIRECTORY, "data")
DATA_FILE = None

# Fonction pour initialiser le fichier de données
def initialData():
	global DATA_FILE
	DATA_FILE = os.path.join(WORKING_DIRECTORY, "settings.json")
	if not os.path.exists(WORKING_DIRECTORY):
		os.makedirs(WORKING_DIRECTORY)
		with open(DATA_FILE, "w") as f:
			json.dump(list(), f, indent=4)

# Classe API pour la gestion des éléments
class API:
	def __init__(self, title = ""):
		self.title = title.title()
		initialData()
	
	def __str__(self):
		return self.title

	# Récupérer la liste des éléments à partir du fichier de données
	def _get_element(self):
		with open(DATA_FILE, "r") as f:
			return json.load(f)

	# Ajouter un élément à la liste
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
			# L'élément existe déjà dans la liste
			return False

	# Supprimer un élément de la liste
	def remove_to_element(self):
		all_elements = self._get_element()
		if self.title in all_elements:
			all_elements.remove(self.title)
			self._write_element(all_elements)

# Fonction pour récupérer les éléments depuis le fichier de données
def GetElement():
	initialData()
	with open(DATA_FILE, "r") as f:
		fullData = json.load(f)
	for mindata in fullData:
		return API(mindata)

# Classe App pour l'interface utilisateur
class App(Tk):

	def __init__(self):
		Tk.__init__(self)
		# global call
		self.fullData = GetElement()
		self.api = None

		# Configuration de la fenêtre principale
		self.title("Task Manager").title()
		self.resizable(width = False, height = False)
		self.geometry("400x400")

		# Champ de saisie pour ajouter un élément
		self.var_entry = StringVar()
		self.entry = Entry(self, textvariable = self.var_entry)
		self.entry.pack(fill = X)

		# Bouton pour ajouter un élément
		self.btn = Button(self, text = "Ajouter un element", command = self.add_item)
		self.btn.pack(fill = X)

		# Liste pour afficher les éléments
		self.var_lstb = StringVar()
		self.lstb = Listbox(self, listvariable = self.var_lstb, selectmode = tkinter.SINGLE)
		self.lstb.pack(fill = BOTH, expand=YES)
		
		# Chargement des éléments depuis le fichier de données
		self.load_template()

		# Bouton pour supprimer des éléments
		self.btn_delete = Button(self, text = "Supprimer le(s) element(s)", command = self.remove_items)
		self.btn_delete.pack(fill = X, side = BOTTOM)

		# Menu contextuel
		self.context_menu = Menu(self, tearoff=0)
		self.context_menu.add_command(label="Modifier l'element")
		self.lstb.bind("<Button-3>", self.show_context_menu)

		# Gestion de l'apparence du bouton lors du survol
		self.btn.bind("<Enter>", self.survol_bouton)
		self.btn_delete.bind("<Enter>", self.survol_bouton)

		self.mainloop()

	# Afficher le menu contextuel
	def show_context_menu(self, event):
		if self.lstb.curselection():
			self.context_menu.post(event.x_root, event.y_root)
		
	# Modifier l'apparence du bouton lors du survol
	def survol_bouton(self, event):
	    self.btn.config(cursor="hand2")
	    self.btn_delete.config(cursor="hand2")

	# Charger les éléments depuis le fichier de données
	def load_template(self):
		with open(DATA_FILE, "r") as f:
			indices = json.load(f)
			for key, value in enumerate(indices):
				self.lstb.insert(key, value)

	# Ajouter un élément à la liste
	def add_item(self):
		if not self.var_entry.get() or len(self.var_entry.get()) > 25:
			# Message d'erreur si l'élément est vide ou trop long
			messagebox.showerror("Attention !", "Quelque chose c'est mal passer l'application n'a pas pu effectuer votre action.")
		else:
			# Appeler la classe API avec le nom de l'élément en argument
			self.api = API(self.var_entry.get())
			if self.api.add_to_element():
				self.api.add_to_element()
				self.lstb.insert(tkinter.END, self.var_entry.get().title())
				self.var_entry.set("")
			else:
				# Message d'information si l'élément existe déjà dans la liste
				messagebox.showinfo("Info !", "L'element existe deja dans la liste.")

	# Supprimer des éléments de la liste
	def remove_items(self):
		# Charger la liste d'éléments depuis le fichier de données
		with open(DATA_FILE, "r") as f:
			content = json.load(f)

			indices = self.lstb.curselection()
			for deleted in indices:
				if 0 <= deleted < len(content):
					del content[deleted]
				self.lstb.delete(deleted)

		# Écrire la liste d'éléments mise à jour dans le fichier de données
		with open(DATA_FILE, "w") as f:
			json.dump(content, f, indent = 4)

# Démarrage de l'application
if __name__ == '__main__':
	app = App()
