from itertools import islice
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import PIL
import pandas
import sqlite3
from datetime import datetime
from pandastable import Table, dialogs
from importlib.resources import files
from whafer.interfacce import Sorgente, Contatto, Gruppo, Messaggio
from whafer.progetti import Progetto

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
genericUserImg = PIL.Image.open(files("whafer.assets").joinpath("generic-user-icon.png"))

class TagFrame(ctk.CTkFrame):
    def __init__(self, parent, immagine: PIL.Image, intestazione: str, descrizione: str, testoPulsante: str, comando: callable):
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0,1), weight=1)

        try:
            self.immagine = ctk.CTkImage(immagine, size=(30,30))
        except self.immagine == None:
            self.immagine = ctk.CTkImage(size=(30,30))

        self.intestazione = ctk.CTkLabel(self, text=intestazione, font=ctk.CTkFont(size=40, weight="bold"), anchor="w", image=self.immagine, compound="left")
        self.descrizione = ctk.CTkLabel(self, text=descrizione, font=ctk.CTkFont(size=20), anchor="w", wraplength=600)
        self.pulsante = ctk.CTkButton(self, text=testoPulsante, command=comando)

        self.intestazione.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.descrizione.grid(row=1, column=0, sticky="w", padx=10, pady=(0,10))
        self.pulsante.grid(row=0, column=1, padx=10, pady=10)

class BaseView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)

class BenvenutoView(BaseView):
    def __init__(self, parent):
        super().__init__(parent)

        self.intestazione = ctk.CTkLabel(self, text="Benvenuto su WhaFeR!", font=ctk.CTkFont(size=40, weight="bold"))
        self.descrizione = ctk.CTkLabel(self, text="Usa i bottoni sulla barra di navigazione laterale per cambiare vista")

        self.intestazione.pack(expand=True, anchor="s")
        self.descrizione.pack(expand=True, anchor="n")

class GruppiView(BaseView):

    def __init__(self, parent, gruppi: list[Gruppo]):
        super().__init__(parent)

        self.gruppi = gruppi
        self.gruppiFiltrati = gruppi
        self.gruppoCorrente = 0
        self.numGruppi = 5

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.intestazione = ctk.CTkLabel(self, text="Gruppi trovati", font=ctk.CTkFont(size=40, weight="bold"))

        opzioniOrdina = ["Data creazione", "Nome"]
        self.ordinamentoCorrente = ctk.StringVar(self, value=opzioniOrdina[0])
        self.versoOrdinamento = ctk.BooleanVar(self, value=False)

        self.ordinaPer = ctk.CTkFrame(self)
        self.ordinaPer.intestazione = ctk.CTkLabel(self.ordinaPer, text="Ordina per")
        self.ordinaPer.scelta = ctk.CTkOptionMenu(self.ordinaPer, values=opzioniOrdina, variable=self.ordinamentoCorrente, command=self.ordina_gruppi)
        self.ordinaPer.verso = ctk.CTkCheckBox(self.ordinaPer, variable=self.versoOrdinamento, onvalue=True, offvalue=False, text="Decrescente?", command=self.ordina_gruppi)

        self.filtro = ctk.StringVar(self)

        self.filtraPer = ctk.CTkFrame(self)
        self.filtraPer.intestazione = ctk.CTkLabel(self.filtraPer, text="Filtra per")
        self.filtraPer.testo = ctk.CTkEntry(self.filtraPer, placeholder_text="Filtra per nome", textvariable=self.filtro)
        self.filtraPer.pulsante = ctk.CTkButton(self.filtraPer, text="Cerca", command=self.filtra_gruppi)

        self.frameGruppi = ctk.CTkScrollableFrame(self)
        
        self.ordina_gruppi()
        self.mostra_gruppi()

        self.framePulsanti = ctk.CTkFrame(self)
        self.frameGruppi.pagIndietro = ctk.CTkButton(self.framePulsanti, text="Pagina precedente", command=self.mostra_pagina_precedente).pack(side="left", anchor="sw", padx=10, pady=10)
        self.frameGruppi.pagAvanti = ctk.CTkButton(self.framePulsanti, text="Pagina successiva", command=self.mostra_pagina_successiva).pack(side="right", anchor="se", padx=10, pady=10)

        self.ordinaPer.verso.pack(side="right", padx=5, pady=5)
        self.ordinaPer.scelta.pack(side="right", padx=5, pady=5)
        self.ordinaPer.intestazione.pack(side="right", fill="both", padx=5, pady=5)
        
        self.filtraPer.intestazione.pack(side="left", padx=5, pady=5)
        self.filtraPer.testo.pack(side="left", padx=5, pady=5)
        self.filtraPer.pulsante.pack(side="left", padx=5, pady=5)

        self.intestazione.grid(row=0, column=0, columnspan=3, padx=(10,0), pady=(10,0), sticky="w")
        self.ordinaPer.grid(row=1, column=1, padx=10, pady=(10,0), sticky="nsew")
        self.filtraPer.grid(row=1, column=2, padx=10, pady=(10,0), sticky="nsew")
        self.frameGruppi.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.framePulsanti.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    def mostra_vista_gruppo(self, gruppo: Gruppo):
        self.destroy()
        self.master.vista = GruppoView(self.master, gruppo)
 
    def mostra_gruppi(self):
        for widget in self.frameGruppi.winfo_children():
            widget.destroy()
        for gruppo in islice(self.gruppiFiltrati, self.gruppoCorrente, self.gruppoCorrente+self.numGruppi):
            gruppoFrame = TagFrame(self.frameGruppi, 
                                               genericUserImg,
                                               gruppo.nome,
                                               f"Creato in data: {gruppo.dataCreazione}",
                                               "Vai al gruppo",
                                               lambda gruppo=gruppo: self.mostra_vista_gruppo(gruppo))
            gruppoFrame.pack(fill="x", padx=10, pady=(10,0))
            ttk.Separator(self.frameGruppi, orient='horizontal').pack(fill="x", padx=10, pady=(10,0))

    def mostra_pagina_successiva(self):
        if self.gruppoCorrente + self.numGruppi <= len(self.gruppiFiltrati):
            self.gruppoCorrente += self.numGruppi
        self.mostra_gruppi()
        
    def mostra_pagina_precedente(self):
        if self.gruppoCorrente - self.numGruppi >= 0:
            self.gruppoCorrente -= self.numGruppi
        self.mostra_gruppi()

    def ordina_gruppi(self, *args):
        opzioni = {
            "Data creazione": lambda gruppo: (gruppo.dataCreazione is None, gruppo.dataCreazione) ,
            "Nome": lambda gruppo: (gruppo.nome is None, gruppo.nome)
        }
        self.gruppiFiltrati.sort(key=opzioni.get(self.ordinamentoCorrente.get()), reverse=self.versoOrdinamento.get())
        self.mostra_gruppi()

    def filtra_gruppi(self):
        gruppiTemp = [gruppo for gruppo in self.gruppi if gruppo.nome is not None]
        self.gruppiFiltrati = [gruppo for gruppo in gruppiTemp if self.filtro.get() in gruppo.nome ]
        self.gruppoCorrente = 0
        self.ordina_gruppi()
        self.mostra_gruppi()

class GruppoView(BaseView):
    def __init__(self, parent, gruppo: Gruppo):
        super().__init__(parent)

        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.gruppo = gruppo

        gruppoImg = ctk.CTkImage(genericUserImg, size=(30,30))

        self.intestazione = ctk.CTkLabel(self, text=gruppo.nome, font=ctk.CTkFont(size=40, weight="bold"), image=gruppoImg, compound="left")

        self.dataCreazione = ctk.CTkLabel(self, text=f"Creato in data: {str(gruppo.dataCreazione)}", justify="left")
        self.creatore = ctk.CTkLabel(self, text=f"Creato da: {gruppo.creatore.nome}", justify="left")

        self.intestazioneMembri = ctk.CTkLabel(self, text="Membri del gruppo", font=ctk.CTkFont(size=30, weight="bold"), justify="left")
        self.intestazioneMessaggi = ctk.CTkLabel(self, text="Messaggi del gruppo", font=ctk.CTkFont(size=30, weight="bold"), justify="left")

        self.frameMembri = ctk.CTkScrollableFrame(self)
        self.frameMessaggi = ctk.CTkScrollableFrame(self)

        self.intestazione.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10,0))
        self.dataCreazione.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(10,0))
        self.creatore.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(10,0))
        self.intestazioneMembri.grid(row= 3, column=0, padx=10, pady=(10, 0))
        self.intestazioneMessaggi.grid(row= 3, column=1, padx=10, pady=(10, 0))
        self.frameMembri.grid(row= 4, column=0, sticky="nsew", padx=10, pady=10)
        self.frameMessaggi.grid(row= 4, column=1, sticky="nsew", padx=10, pady=10)

        self.mostra_membri()
        self.mostra_messaggi()

    def mostra_membri(self):
        for widget in self.frameMembri.winfo_children():
            widget.destroy()
        self.frameMembri.intestazioneAmministratori = ctk.CTkLabel(self.frameMembri, text="Amministratori", font=ctk.CTkFont(size=20, weight="bold"))
        self.frameMembri.intestazioneAmministratori.pack(fill="x", padx=10, pady=(10,0))
        amministratori = self.gruppo.amministratori
        if amministratori:
            for amministratore in self.gruppo.amministratori:
                membroFrame = TagFrame(self.frameMembri, 
                                                genericUserImg,
                                                amministratore.numeroTelefonico,
                                                "Lorem Ipsum",
                                                "Vai al contatto",
                                                None)
                membroFrame.pack(fill="x", padx=10, pady=(10,0))
                ttk.Separator(self.frameMembri, orient='horizontal').pack(fill="x", padx=10, pady=(10,0))
        else:
            membroFrame = ctk.CTkLabel(self.frameMembri, text="Non trovati")
            membroFrame.pack(fill="x", padx=10, pady=(10,0))
        self.frameMembri.intestazionePartecipanti = ctk.CTkLabel(self.frameMembri, text="Membri", font=ctk.CTkFont(size=20, weight="bold"))
        self.frameMembri.intestazionePartecipanti.pack(fill="x", padx=10, pady=(10,0))
        partecipanti = self.gruppo.partecipanti
        if partecipanti:
            for partecipante in self.gruppo.partecipanti:
                membroFrame = TagFrame(self.frameMembri, 
                                                genericUserImg,
                                                partecipante.numeroTelefonico,
                                                "Lorem Ipsum",
                                                "Vai al contatto",
                                                None)
                membroFrame.pack(fill="x", padx=10, pady=(10,0))
                ttk.Separator(self.frameMembri, orient='horizontal').pack(fill="x", padx=10, pady=(10,0))
        else:
            membroFrame = ctk.CTkLabel(self.frameMembri, text="Non trovati")
            membroFrame.pack(fill="x", padx=10, pady=(10,0))

    def mostra_messaggi(self):
        for widget in self.frameMessaggi.winfo_children():
            widget.destroy()
        messaggi = self.gruppo.messaggi
        if messaggi:
            for messaggio in messaggi[0:10]:
                messaggioFrame = TagFrame(self.frameMessaggi, 
                                                genericUserImg,
                                                "Messaggio",
                                                messaggio.contenuto,
                                                "Vai al messaggio",
                                                None)
                messaggioFrame.pack(fill="x", padx=10, pady=(10,0))
                ttk.Separator(self.frameMessaggi, orient='horizontal').pack(fill="x", padx=10, pady=(10,0))
        else:
            messaggioFrame = ctk.CTkLabel(self.frameMessaggi, )

class ContattiView(BaseView):

    def __init__(self, parent, contatti: list[Contatto]):
        super().__init__(parent)

        self.contatti = contatti
        self.contattiFiltrati = contatti
        self.contattoCorrente = 0
        self.numContatti = 5

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.intestazione = ctk.CTkLabel(self, text="Contatti trovati", font=ctk.CTkFont(size=40, weight="bold"))

        opzioniOrdina = ["Numero telefonico", "Nome"]
        self.ordinamentoCorrente = ctk.StringVar(self, value=opzioniOrdina[0])
        self.versoOrdinamento = ctk.BooleanVar(self, value=False)

        self.ordinaPer = ctk.CTkFrame(self)
        self.ordinaPer.intestazione = ctk.CTkLabel(self.ordinaPer, text="Ordina per")
        self.ordinaPer.scelta = ctk.CTkOptionMenu(self.ordinaPer, values=opzioniOrdina, variable=self.ordinamentoCorrente, command=self.ordina_contatti)
        self.ordinaPer.verso = ctk.CTkCheckBox(self.ordinaPer, variable=self.versoOrdinamento, onvalue=True, offvalue=False, text="Decrescente?", command=self.ordina_contatti)

        self.filtro = ctk.StringVar(self)

        self.filtraPer = ctk.CTkFrame(self)
        self.filtraPer.intestazione = ctk.CTkLabel(self.filtraPer, text="Filtra per")
        self.filtraPer.testo = ctk.CTkEntry(self.filtraPer, placeholder_text="Filtra per nome", textvariable=self.filtro)
        self.filtraPer.pulsante = ctk.CTkButton(self.filtraPer, text="Cerca", command=self.filtra_contatti)

        self.frameContatti = ctk.CTkScrollableFrame(self)
        
        self.ordina_contatti()
        self.mostra_contatti()

        self.framePulsanti = ctk.CTkFrame(self)
        self.frameContatti.pagIndietro = ctk.CTkButton(self.framePulsanti, text="Pagina precedente", command=self.mostra_pagina_precedente).pack(side="left", anchor="sw", padx=10, pady=10)
        self.frameContatti.pagAvanti = ctk.CTkButton(self.framePulsanti, text="Pagina successiva", command=self.mostra_pagina_successiva).pack(side="right", anchor="se", padx=10, pady=10)

        self.ordinaPer.verso.pack(side="right", padx=5, pady=5)
        self.ordinaPer.scelta.pack(side="right", padx=5, pady=5)
        self.ordinaPer.intestazione.pack(side="right", fill="both", padx=5, pady=5)
        
        self.filtraPer.intestazione.pack(side="left", padx=5, pady=5)
        self.filtraPer.testo.pack(side="left", padx=5, pady=5)
        self.filtraPer.pulsante.pack(side="left", padx=5, pady=5)

        self.intestazione.grid(row=0, column=0, columnspan=3, padx=(10,0), pady=(10,0), sticky="w")
        self.ordinaPer.grid(row=1, column=1, padx=10, pady=(10,0), sticky="nsew")
        self.filtraPer.grid(row=1, column=2, padx=10, pady=(10,0), sticky="nsew")
        self.frameContatti.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.framePulsanti.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    def mostra_vista_contatto(self, contatto: Contatto):
        self.destroy()
        self.master.vista = ContattoView(self.master, contatto)
 
    def mostra_contatti(self):
        for widget in self.frameContatti.winfo_children():
            widget.destroy()
        genericUserImg = PIL.Image.open(files("whafer.assets").joinpath("generic-user-icon.png"))
        for contatto in islice(self.contattiFiltrati, self.contattoCorrente, self.contattoCorrente+self.numContatti):
            self.frameContatti.contatto = TagFrame(self.frameContatti, 
                                               genericUserImg,
                                               contatto.nome,
                                               f"Numero telefonico: {contatto.numeroTelefonico}",
                                               "Vai al contatto",
                                               lambda contatto=contatto: self.mostra_vista_contatto(contatto))
            self.frameContatti.contatto.pack(fill="x", padx=10, pady=(10,0))
            ttk.Separator(self.frameContatti, orient='horizontal').pack(fill="x", padx=10, pady=(10,0))

    def mostra_pagina_successiva(self):
        if self.contattoCorrente + self.numContatti <= len(self.contattiFiltrati):
            self.contattoCorrente += self.numContatti
        self.mostra_contatti()
        
    def mostra_pagina_precedente(self):
        if self.contattoCorrente - self.numContatti >= 0:
            self.contattoCorrente -= self.numContatti
        self.mostra_contatti()

    def ordina_contatti(self, *args):
        opzioni = {
            "Numero telefonico": lambda contatto: (contatto.numeroTelefonico is None, contatto.numeroTelefonico) ,
            "Nome": lambda contatto: (contatto.nome is None, contatto.nome)
        }
        self.contattiFiltrati.sort(key=opzioni.get(self.ordinamentoCorrente.get()), reverse=self.versoOrdinamento.get())
        self.mostra_contatti()
        pass

    def filtra_contatti(self):
        contattiTemp = [contatto for contatto in self.contatti if contatto.nome is not None]
        self.contattiFiltrati = [contatto for contatto in contattiTemp if self.filtro.get() in contatto.nome ]
        self.contattoCorrente = 0
        self.ordina_contatti()
        self.mostra_contatti()
        pass

class ContattoView(BaseView):
    def __init__(self, parent, contatto: Contatto):
        super().__init__(parent)

        self.intestazione = ctk.CTkLabel(self, text=contatto.nome, font=ctk.CTkFont(size=40, weight="bold"))

        self.numeroTelefonico = ctk.CTkLabel(self, text=f"Numero telefonico: {str(contatto.numeroTelefonico)}", justify="left")

        self.intestazione.pack(anchor="w", padx=(10,0), pady=(10,0))
        self.numeroTelefonico.pack(anchor="w", padx=(10,0), pady=(10,0))

class ContenutiView(BaseView):
    def __init__(self, parent, progetto: Progetto):
        super().__init__(parent)
        self.frameOggetti = ctk.CTkScrollableFrame(self)
        self.frameOggetti.pack(fill="both", expand=True, padx=10, pady=10)

        self.progetto = progetto
        self.db = sqlite3.connect(str(self.progetto.percorso / "sorgenti" / "msgstore.db"))

        self.contatti = pandas.read_sql_query("SELECT * FROM jid LEFT JOIN chat_view ON chat_view.raw_string_jid = jid.raw_string WHERE jid.type = 0", self.db)

        self.intestazioneContatti = ctk.CTkLabel(self.frameOggetti, text="Contatti", font=ctk.CTkFont(size=40, weight="bold"), justify="left")
        self.frameContatti = ctk.CTkFrame(self.frameOggetti)
        self.contattiTabella = Table(self.frameContatti, dataframe=self.contatti)
        self.pulsanteContatti = ctk.CTkButton(self.frameOggetti, text="Esporta contatti", command=self.reporta_contatti)
        self.gruppi = pandas.read_sql_query("SELECT * FROM jid JOIN chat_view ON chat_view.raw_string_jid = jid.raw_string WHERE jid.type = 1", self.db)
 
        self.intestazioneGruppi = ctk.CTkLabel(self.frameOggetti, text="Gruppi", font=ctk.CTkFont(size=40, weight="bold"), justify="left")
        self.frameGruppi = ctk.CTkFrame(self.frameOggetti)
        self.gruppiTabella = Table(self.frameGruppi, dataframe=self.gruppi)
        self.pulsanteGruppi = ctk.CTkButton(self.frameOggetti, text="Esporta gruppi", command=self.reporta_gruppi)

        self.messaggi = pandas.read_sql_query("SELECT * FROM message_view", self.db)

        self.intestazioneMessaggi = ctk.CTkLabel(self.frameOggetti, text="Messaggi", font=ctk.CTkFont(size=40, weight="bold"), justify="left")
        self.frameMessaggi = ctk.CTkFrame(self.frameOggetti)
        self.messaggiTabella = Table(self.frameMessaggi, dataframe=self.messaggi)
        self.pulsanteMessaggi = ctk.CTkButton(self.frameOggetti, text="Esporta messaggi", command=self.reporta_messaggi)

        self.intestazioneContatti.pack(anchor="w", padx=10, pady=(10,0))
        self.frameContatti.pack(fill="x", padx=10, pady=(10,0))
        self.contattiTabella.show()
        self.contattiTabella.redraw()
        self.pulsanteContatti.pack(anchor="w", padx=10, pady=(10,0))

        self.intestazioneGruppi.pack(anchor="w", padx=10, pady=(10,0))
        self.frameGruppi.pack(fill="x", padx=10, pady=(10,0))
        self.gruppiTabella.show()
        self.gruppiTabella.redraw()
        self.pulsanteGruppi.pack(anchor="w", padx=10, pady=(10,0))

        self.intestazioneMessaggi.pack(anchor="w", padx=10, pady=(10,0))
        self.frameMessaggi.pack(fill="x", padx=10, pady=(10,0))
        self.messaggiTabella.show()
        self.messaggiTabella.redraw()
        self.pulsanteMessaggi.pack(anchor="w", padx=10, pady=(10,0))

    def filtra_contatti(self):
        pass

    def filtra_gruppi(self):
        pass

    def filtra_messaggi(self):
        pass

    def reporta_contatti(self):
        percorso = (self.progetto.percorso / "reports" / f"contatti_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv")
        
        with open(percorso, mode="wb") as file:
            self.contatti.to_csv(file)

    def reporta_gruppi(self):
        percorso = (self.progetto.percorso / "reports" / f"gruppi_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv")
        
        with open(percorso, mode="wb") as file:
            self.gruppi.to_csv(file)

    def reporta_messaggi(self):
        percorso = (self.progetto.percorso / "reports" / f"messaggi_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv")
        
        with open(percorso, mode="wb") as file:
            self.messaggi.to_csv(file)

class Applicazione(ctk.CTkFrame):
    def __init__(self, parent, progetto: Progetto):
        super().__init__(parent)
        self.pack(expand=True, fill="both")

        self.progetto = progetto

        self.navbar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.navbar.pack(side="left", fill="both", ipadx=10)

        self.intestazione = ctk.CTkLabel(self.navbar, text="WhaFeR", font=ctk.CTkFont(size=20, weight="bold"), width=200)
        self.pulsanteGruppo = ctk.CTkButton(self.navbar, text="Gruppi", command=self.mostra_vista_gruppi)
        self.pulsanteContatto = ctk.CTkButton(self.navbar, text="Contatti", command=self.mostra_vista_contatti)
        self.pulsanteMedia = ctk.CTkButton(self.navbar, state="disabled", text="Media")
        self.pulsanteArtefatti = ctk.CTkButton(self.navbar, state="disabled", text="Lista artefatti estratti")
        self.pulsanteContenuti = ctk.CTkButton(self.navbar, text="Mostra contenuti", command=self.mostra_vista_contenuti)
        self.pulsanteImpostazioni = ctk.CTkButton(self.navbar, state="disabled", text="Impostazioni")

        self.vista = BenvenutoView(self)

        self.intestazione.pack(fill="x", pady=10, padx=10)
        self.pulsanteGruppo.pack(fill="x", pady=10, padx=10)
        self.pulsanteContatto.pack(fill="x", pady=10, padx=10)
        self.pulsanteMedia.pack(fill="x", pady=10, padx=10)
        self.pulsanteArtefatti.pack(fill="x", pady=10, padx=10)
        self.pulsanteContenuti.pack(fill="x", pady=10, padx=10)
        self.pulsanteImpostazioni.pack(fill="x", pady=10, padx=10)

    def mostra_vista_gruppi(self):
        self.vista.destroy()
        self.vista = GruppiView(self, self.progetto.sorgente.gruppi)

    def mostra_vista_contatti(self):
        self.vista.destroy()
        self.vista = ContattiView(self, self.progetto.sorgente.contatti)
    
    def mostra_vista_contenuti(self):
        self.vista.destroy()
        self.vista = ContenutiView(self, self.progetto)

class Introduzione(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        whaimage = ctk.CTkImage(PIL.Image.open(files("whafer.assets").joinpath("whatsapp.png")), size=(30, 30))
        gdriveimage = ctk.CTkImage(PIL.Image.open(files("whafer.assets").joinpath("GoogleDrive.png")), size=(40, 40))
        androidimage = ctk.CTkImage(PIL.Image.open(files("whafer.assets").joinpath("android.png")), size=(40, 40))
        localimage = ctk.CTkImage(PIL.Image.open(files("whafer.assets").joinpath("search.png")), size=(40, 40))

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.title_label = ctk.CTkLabel(self.sidebar_frame, text="WhaFer", font=ctk.CTkFont(size=20, weight="bold"), image=whaimage, compound="right", padx=10)
        self.title_label.grid(row=0, column=0, padx=5, pady=5)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                             command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                     command=self.change_scaling_event)

        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))
        
        self.frame_azioni = ctk.CTkFrame(self)
        self.frame_azioni.grid(row=0, column=1, padx=150, pady=150)
        self.frame_azioni.grid_columnconfigure((0, 2), weight=1)
        self.frame_azioni.grid_rowconfigure((0, 2), weight=1)

        # Sezione estrai

        self.estrazioneIntestazione = ctk.CTkLabel(self.frame_azioni, text="Estrai i dati da...",font=ctk.CTkFont(size=30))
        self.estrazioneIntestazione.grid(row=0, column=0, sticky="s", padx=10, pady=10)

        self.estrazioneFrameBottoni = ctk.CTkFrame(self.frame_azioni)
        self.estrazioneFrameBottoni.grid(row=1, column=0, sticky="ns", padx=10, pady=10, ipadx=100)

        # bottone per caricare il progetto da Google Drive
        self.pulsanteGoogleDrive = ctk.CTkButton(self.estrazioneFrameBottoni, state="disabled", text="Google Drive", image=gdriveimage, compound="right", font=ctk.CTkFont(size=15))
        self.pulsanteGoogleDrive.pack(fill="x",padx=10, pady=10)

        # bottone per caricare il progetto da un telefono android
        self.pulsanteAndroid = ctk.CTkButton(self.estrazioneFrameBottoni, state="disabled", text="Android", image=androidimage, compound="right", font=ctk.CTkFont(size=15))
        self.pulsanteAndroid.pack(fill="x", padx=10, pady=(0,10))

        # bottone per caricare il progetto dal local storage
        self.pulsanteLocal = ctk.CTkButton(self.estrazioneFrameBottoni, text="Local Storage", image=localimage, compound="right", font=ctk.CTkFont(size=15), command=self.estrai_locale)
        self.pulsanteLocal.pack(fill="x", padx=10, pady=(0,10))

        self.separatore = ttk.Separator(self.frame_azioni, orient="vertical")
        self.separatore.grid(row=0, column=1, rowspan=3, sticky="ns", padx=5, pady=25)

        self.progettoIntestazione = ctk.CTkLabel(self.frame_azioni, text="Apri un progetto",font=ctk.CTkFont(size=30))
        self.progettoIntestazione.grid(row=0, column=2, sticky="s", padx=10, pady=10)

        self.progettoPulsante = ctk.CTkButton(self.frame_azioni, text="Seleziona un progetto", command=self.apri_progetto)
        self.progettoPulsante.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
    
    def apri_progetto(self):
        percorsoProgetto = tk.filedialog.askdirectory(title="Seleziona un progetto precedentemente creato")
        progetto = Progetto(percorsoProgetto)
        self.master.main = Applicazione(self.master, progetto)
        self.destroy()

    def estrai_locale(self):
        artefatti = tk.filedialog.askopenfilenames(title="Seleziona gli artefatti da importare", multiple=True)
        percorsoProgetto = tk.filedialog.askdirectory(title="Seleziona una cartella vuota in cui creare il progetto")
        sorgenti = [artefatto for artefatto in artefatti if artefatto.endswith(".db")]
        encrypted = [artefatto for artefatto in artefatti if ".crypt" in artefatto]
        progetto = Progetto(percorsoProgetto, sorgenti=sorgenti, encrypted=encrypted)
        self.master.main = Applicazione(self.master, progetto)
        self.destroy()

def main():
    app = ctk.CTk()
    app.title("WhaFeR - WhatsApp Forensic Reporter")
    app.geometry(f"{1100}x{580}")
    app.main = Introduzione(app).pack(fill="both", expand=True)
    app.mainloop()

if __name__ == "__main__":
    main()
