#!/usr/bin/env python3
# Created by Ber1y - refactor complet : POO, Tkinter/ttk, json, gestion d'erreurs
"""Task Manager - petit gestionnaire de tâches avec interface graphique.

Architecture :
    * TaskStore : couche de persistance (lecture/écriture JSON, migration).
    * TaskDialog : fenêtre modale d'ajout / édition d'une tâche.
    * App        : interface Tkinter/ttk (affichage, actions utilisateur).
"""

import os
import json
import uuid
import logging
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DATA_DIRECTORY = os.path.join(CURRENT_DIRECTORY, "data")
DATA_FILE = os.path.join(DATA_DIRECTORY, "tasks.json")
LEGACY_FILE = os.path.join(DATA_DIRECTORY, "settings.json")  # ancien format

MAX_TITLE_LENGTH = 80
PRIORITIES = ["Basse", "Normale", "Haute"]
DEFAULT_PRIORITY = "Normale"
PRIORITY_ORDER = {"Haute": 0, "Normale": 1, "Basse": 2}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("task-manager")


# ---------------------------------------------------------------------------
# Couche de données
# ---------------------------------------------------------------------------
class TaskStore:
    """Gère le chargement et la sauvegarde des tâches dans un fichier JSON."""

    def __init__(self, path=DATA_FILE):
        self.path = path
        self.tasks = []
        self._ensure_storage()
        self.load()

    def _ensure_storage(self):
        """Crée le répertoire de données et le fichier s'ils n'existent pas."""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            # Migration depuis l'ancien fichier (liste de chaînes) si présent.
            if os.path.exists(LEGACY_FILE):
                self._migrate_legacy()
            else:
                self._write([])

    def _migrate_legacy(self):
        """Convertit l'ancien format settings.json (liste de titres)."""
        try:
            with open(LEGACY_FILE, "r", encoding="utf-8") as f:
                old = json.load(f)
            migrated = [self._new_task(str(title)) for title in old]
            self._write(migrated)
            logger.info("Migration de %d ancienne(s) tâche(s) réussie.", len(migrated))
        except (OSError, ValueError) as exc:
            logger.warning("Migration impossible (%s), démarrage à vide.", exc)
            self._write([])

    @staticmethod
    def _new_task(title, priority=DEFAULT_PRIORITY, done=False):
        """Construit un dictionnaire tâche normalisé."""
        now = datetime.now().isoformat(timespec="seconds")
        return {
            "id": uuid.uuid4().hex,
            "title": title.strip(),
            "priority": priority if priority in PRIORITIES else DEFAULT_PRIORITY,
            "done": bool(done),
            "created_at": now,
            "updated_at": now,
        }

    def _read(self):
        """Lit le fichier JSON en tolérant les corruptions."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("format inattendu")
            return data
        except (OSError, ValueError) as exc:
            logger.error("Lecture impossible (%s), réinitialisation.", exc)
            return []

    def _write(self, data):
        """Écrit la liste de tâches sur le disque."""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load(self):
        """Recharge les tâches depuis le disque en mémoire."""
        self.tasks = self._read()
        return self.tasks

    def save(self):
        """Persiste l'état mémoire sur le disque."""
        self._write(self.tasks)

    # --- Opérations CRUD ---------------------------------------------------
    def title_exists(self, title, ignore_id=None):
        """Vrai si une tâche porte déjà ce titre (comparaison insensible à la casse)."""
        needle = title.strip().casefold()
        return any(
            t["title"].casefold() == needle and t["id"] != ignore_id
            for t in self.tasks
        )

    def add(self, title, priority=DEFAULT_PRIORITY):
        """Ajoute une tâche ; renvoie la tâche créée ou None si doublon."""
        if self.title_exists(title):
            return None
        task = self._new_task(title, priority)
        self.tasks.append(task)
        self.save()
        return task

    def update(self, task_id, title=None, priority=None, done=None):
        """Met à jour les champs fournis d'une tâche existante."""
        task = self.get(task_id)
        if task is None:
            return None
        if title is not None:
            task["title"] = title.strip()
        if priority is not None:
            task["priority"] = priority
        if done is not None:
            task["done"] = bool(done)
        task["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.save()
        return task

    def delete(self, task_id):
        """Supprime une tâche par son identifiant."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        if len(self.tasks) != before:
            self.save()
            return True
        return False

    def get(self, task_id):
        """Retourne la tâche correspondant à l'identifiant, ou None."""
        return next((t for t in self.tasks if t["id"] == task_id), None)


# ---------------------------------------------------------------------------
# Boîte de dialogue d'ajout / édition
# ---------------------------------------------------------------------------
class TaskDialog(tk.Toplevel):
    """Fenêtre modale pour saisir ou modifier une tâche.

    Après fermeture, l'attribut ``result`` contient soit ``None`` (annulation),
    soit un dictionnaire ``{"title": ..., "priority": ...}``.
    """

    def __init__(self, parent, title="Nouvelle tâche", task=None):
        super().__init__(parent)
        self.result = None

        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()  # modal

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Intitulé :").grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.var_title = tk.StringVar(value=task["title"] if task else "")
        entry = ttk.Entry(frame, textvariable=self.var_title, width=38)
        entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text="Priorité :").grid(row=2, column=0, sticky="w", pady=(0, 2))
        self.var_priority = tk.StringVar(value=task["priority"] if task else DEFAULT_PRIORITY)
        combo = ttk.Combobox(
            frame,
            textvariable=self.var_priority,
            values=PRIORITIES,
            state="readonly",
            width=15,
        )
        combo.grid(row=3, column=0, sticky="w", pady=(0, 12))

        btns = ttk.Frame(frame)
        btns.grid(row=4, column=0, columnspan=2, sticky="e")
        ttk.Button(btns, text="Annuler", command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text="Valider", command=self._validate).pack(side=tk.RIGHT)

        # Raccourcis clavier
        self.bind("<Return>", lambda e: self._validate())
        self.bind("<Escape>", lambda e: self._cancel())

        entry.focus_set()
        entry.icursor(tk.END)
        self._center_on(parent)
        self.wait_window(self)

    def _center_on(self, parent):
        """Centre la fenêtre au-dessus de la fenêtre parente."""
        self.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _validate(self):
        title = self.var_title.get().strip()
        if not title:
            messagebox.showwarning("Champ vide", "L'intitulé ne peut pas être vide.", parent=self)
            return
        if len(title) > MAX_TITLE_LENGTH:
            messagebox.showwarning(
                "Trop long",
                f"L'intitulé ne doit pas dépasser {MAX_TITLE_LENGTH} caractères.",
                parent=self,
            )
            return
        self.result = {"title": title, "priority": self.var_priority.get()}
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# ---------------------------------------------------------------------------
# Application principale
# ---------------------------------------------------------------------------
class App(tk.Tk):
    """Fenêtre principale du gestionnaire de tâches."""

    STATUS_DONE = "✔"
    STATUS_TODO = "○"

    def __init__(self):
        super().__init__()
        self.store = TaskStore()
        self.sort_state = {"column": None, "reverse": False}

        self.title("Task Manager")
        self.geometry("560x460")
        self.minsize(460, 360)

        self._setup_style()
        self._build_toolbar()
        self._build_tree()
        self._build_statusbar()
        self._build_menu()
        self._bind_shortcuts()

        self.refresh()

    # --- Construction de l'UI ---------------------------------------------
    def _setup_style(self):
        style = ttk.Style(self)
        # 'clam' est disponible partout et plus moderne que le thème par défaut.
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", rowheight=24)

    def _build_toolbar(self):
        bar = ttk.Frame(self, padding=(8, 8, 8, 4))
        bar.pack(fill=tk.X)

        self.var_entry = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.var_entry)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.bind("<Return>", lambda e: self.quick_add())
        self.entry = entry

        self.var_priority = tk.StringVar(value=DEFAULT_PRIORITY)
        ttk.Combobox(
            bar,
            textvariable=self.var_priority,
            values=PRIORITIES,
            state="readonly",
            width=10,
        ).pack(side=tk.LEFT, padx=6)

        ttk.Button(bar, text="Ajouter", command=self.quick_add).pack(side=tk.LEFT)

        # Barre de recherche
        search_bar = ttk.Frame(self, padding=(8, 0, 8, 4))
        search_bar.pack(fill=tk.X)
        ttk.Label(search_bar, text="Rechercher :").pack(side=tk.LEFT)
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(search_bar, textvariable=self.var_search).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0)
        )

    def _build_tree(self):
        container = ttk.Frame(self, padding=(8, 0, 8, 4))
        container.pack(fill=tk.BOTH, expand=True)

        columns = ("status", "priority", "title")
        self.tree = ttk.Treeview(
            container, columns=columns, show="headings", selectmode="extended"
        )
        self.tree.heading("status", text="État", command=lambda: self.sort_by("done"))
        self.tree.heading("priority", text="Priorité", command=lambda: self.sort_by("priority"))
        self.tree.heading("title", text="Tâche", command=lambda: self.sort_by("title"))
        self.tree.column("status", width=50, anchor="center", stretch=False)
        self.tree.column("priority", width=90, anchor="center", stretch=False)
        self.tree.column("title", width=380, anchor="w")

        scroll = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Couleurs : tâches faites grisées, priorité haute en rouge.
        self.tree.tag_configure("done", foreground="#8a8a8a")
        self.tree.tag_configure("haute", foreground="#c0392b")

        self.tree.bind("<Double-1>", lambda e: self.toggle_done())
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _build_statusbar(self):
        self.var_status = tk.StringVar()
        ttk.Label(
            self, textvariable=self.var_status, anchor="w", padding=(8, 2), relief="sunken"
        ).pack(fill=tk.X, side=tk.BOTTOM)

    def _build_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Basculer fait / à faire", command=self.toggle_done)
        self.context_menu.add_command(label="Modifier…", command=self.edit_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Supprimer", command=self.remove_items)

    def _bind_shortcuts(self):
        self.bind("<Delete>", lambda e: self.remove_items())
        self.bind("<F2>", lambda e: self.edit_item())
        self.bind("<Control-n>", lambda e: self.entry.focus_set())
        self.bind("<space>", self._space_toggle)

    # --- Helpers -----------------------------------------------------------
    def _space_toggle(self, event):
        # Ne pas capturer la barre d'espace quand on tape dans un champ.
        if isinstance(event.widget, (ttk.Entry, tk.Entry)):
            return
        self.toggle_done()

    def _show_context_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            if row not in self.tree.selection():
                self.tree.selection_set(row)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def _selected_ids(self):
        return list(self.tree.selection())

    def _visible_tasks(self):
        """Retourne les tâches filtrées par la recherche et triées."""
        needle = self.var_search.get().strip().casefold()
        tasks = [t for t in self.store.tasks if needle in t["title"].casefold()]

        column = self.sort_state["column"]
        if column == "priority":
            tasks.sort(key=lambda t: PRIORITY_ORDER.get(t["priority"], 1),
                       reverse=self.sort_state["reverse"])
        elif column == "title":
            tasks.sort(key=lambda t: t["title"].casefold(),
                       reverse=self.sort_state["reverse"])
        elif column == "done":
            tasks.sort(key=lambda t: t["done"], reverse=self.sort_state["reverse"])
        else:
            # Tri par défaut : à faire d'abord, puis par priorité décroissante.
            tasks.sort(key=lambda t: (t["done"], PRIORITY_ORDER.get(t["priority"], 1)))
        return tasks

    # --- Rendu -------------------------------------------------------------
    def refresh(self):
        """Redessine la liste des tâches et la barre de statut."""
        selected = set(self.tree.selection())
        self.tree.delete(*self.tree.get_children())

        for task in self._visible_tasks():
            status = self.STATUS_DONE if task["done"] else self.STATUS_TODO
            tags = []
            if task["done"]:
                tags.append("done")
            elif task["priority"] == "Haute":
                tags.append("haute")
            self.tree.insert(
                "", tk.END, iid=task["id"],
                values=(status, task["priority"], task["title"]),
                tags=tags,
            )
            if task["id"] in selected:
                self.tree.selection_add(task["id"])

        total = len(self.store.tasks)
        done = sum(1 for t in self.store.tasks if t["done"])
        self.var_status.set(f"{total} tâche(s) — {done} faite(s), {total - done} à faire")

    def sort_by(self, column):
        """Bascule le tri sur la colonne demandée."""
        if self.sort_state["column"] == column:
            self.sort_state["reverse"] = not self.sort_state["reverse"]
        else:
            self.sort_state = {"column": column, "reverse": False}
        self.refresh()

    # --- Actions -----------------------------------------------------------
    def quick_add(self):
        """Ajoute une tâche depuis le champ de la barre d'outils."""
        title = self.var_entry.get().strip()
        if not title:
            messagebox.showwarning("Champ vide", "Saisissez un intitulé de tâche.")
            return
        if len(title) > MAX_TITLE_LENGTH:
            messagebox.showwarning(
                "Trop long",
                f"L'intitulé ne doit pas dépasser {MAX_TITLE_LENGTH} caractères.",
            )
            return
        task = self.store.add(title, self.var_priority.get())
        if task is None:
            messagebox.showinfo("Doublon", "Cette tâche existe déjà dans la liste.")
            return
        self.var_entry.set("")
        self.refresh()

    def edit_item(self):
        """Ouvre la boîte de dialogue d'édition sur la tâche sélectionnée."""
        ids = self._selected_ids()
        if len(ids) != 1:
            messagebox.showinfo("Sélection", "Sélectionnez une seule tâche à modifier.")
            return
        task = self.store.get(ids[0])
        if task is None:
            return
        dialog = TaskDialog(self, title="Modifier la tâche", task=task)
        if dialog.result is None:
            return
        new_title = dialog.result["title"]
        if self.store.title_exists(new_title, ignore_id=task["id"]):
            messagebox.showinfo("Doublon", "Une autre tâche porte déjà ce titre.")
            return
        self.store.update(task["id"], title=new_title, priority=dialog.result["priority"])
        self.refresh()

    def toggle_done(self):
        """Inverse l'état fait / à faire des tâches sélectionnées."""
        for task_id in self._selected_ids():
            task = self.store.get(task_id)
            if task is not None:
                self.store.update(task_id, done=not task["done"])
        self.refresh()

    def remove_items(self):
        """Supprime les tâches sélectionnées après confirmation."""
        ids = self._selected_ids()
        if not ids:
            messagebox.showinfo("Sélection", "Sélectionnez au moins une tâche à supprimer.")
            return
        libelle = "cette tâche" if len(ids) == 1 else f"ces {len(ids)} tâches"
        if not messagebox.askyesno("Confirmation", f"Supprimer {libelle} ?"):
            return
        for task_id in ids:
            self.store.delete(task_id)
        self.refresh()


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    App().mainloop()
