from __future__ import annotations
from datetime import datetime
from whafer.costanti import TIPI_CONTATTI, TIPI_PARTECIPANTI
from whafer.interfacce import Contatto, Gruppo, Messaggio
import sqlite3

class SorgenteDB():
    msgstore: sqlite3.Connection
    wa: sqlite3.Connection|None

    def __init__(self, msgstore: sqlite3.Connection|str, wa: sqlite3.Connection|str|None = None):
        try:
            self.msgstore = sqlite3.connect(msgstore)
        except TypeError:
            self.msgstore = msgstore

        try:
            self.wa = sqlite3.connect(wa)
        except TypeError:
            self.wa = wa

    @property
    def contatti(self)->list[Contatto]:
        #TODO nome dei contatti
        cursore = self.msgstore.cursor()
        cursore.execute("SELECT _id, user "
                        "FROM jid "
                        f"WHERE type = {TIPI_CONTATTI.get('Contatto')}")
        _id, numeriTelefonici = zip(*cursore.fetchall())
        nomi = numeriTelefonici
        contatti = list(map(ContattoDB, _id, numeriTelefonici, nomi))
        return contatti
    
    @property
    def gruppi(self)->list[Gruppo]:
        cursore = self.msgstore.cursor()
        cursore.execute("SELECT jid._id, jid.user, chat_view.subject, chat_view.created_timestamp "
                        "FROM jid "
                        "JOIN chat_view "
                        "ON jid.raw_string = chat_view.raw_string_jid "
                        f"WHERE jid.type = {TIPI_CONTATTI.get('Gruppo')}")
        _id, numeri, nomi, timestamp= zip(*cursore.fetchall())
        timestamp = [datetime.fromtimestamp(ts/1000) if ts is not None else None for ts in timestamp]
        gruppi = list(map(GruppoDB, _id, numeri, nomi, timestamp))
        for gruppo in gruppi:
            gruppo.msgstore = self.msgstore
        return gruppi
    
    @property
    def gruppi_raw(self)->list:
        cursore = self.msgstore.cursor()
        cursore.execute("SELECT * "
                        "FROM jid "
                        "JOIN chat_view "
                        "ON chat_view.raw_string_jid = jid.raw_string "
                        f"WHERE jid.type = {TIPI_CONTATTI['Gruppo']}")
        risultati = cursore.fetchall()
        return risultati
    
    @property
    def contatti_raw(self)->list:
        cursore = self.msgstore.cursor()
        cursore.execute("SELECT * "
                        "FROM jid "
                        "JOIN chat_view "
                        "ON chat_view.raw_string_jid = jid.raw_string "
                        f"WHERE jid.type = {TIPI_CONTATTI['Contatto']}")
        risultati = cursore.fetchall()
        return risultati
    
    @property
    def messaggi_raw(self)->list:
        cursore = self.msgstore.cursor()

        risultati = cursore.fetchall()
        return risultati

class ContattoDB():
    _id: int
    numeroTelefonico: str
    nome: str

    def __init__(self, _id: int, numeroTelefonico: str, nome: str):
        self._id = _id
        self.numeroTelefonico = numeroTelefonico
        self.nome = nome

    @property
    def gruppi(self)->list[Gruppo]:
        pass

    @property
    def messaggi(self)->list[Messaggio]:
        pass

class GruppoDB():
    _id: int
    numeroTelefonico: str
    nome: str
    dataCreazione: datetime
    msgstore: sqlite3.Connection

    def __init__(self, _id: int, numeroTelefonico: str, nome: str, dataCreazione: datetime):
        self._id = _id
        self.numeroTelefonico = numeroTelefonico
        self.nome = nome
        self.dataCreazione = dataCreazione

    @property
    def partecipanti(self)->list[Contatto]:
        cursore = self.msgstore.cursor()
        cursore.execute("SELECT contacts._id, contacts.user "
                        "FROM group_participants "
                        "JOIN jid groups "
                        "ON group_participants.gjid = groups.raw_string "
                        "JOIN jid contacts "
                        "ON group_participants.jid = contacts.raw_string "
                        f"WHERE groups.user = \"{self.numeroTelefonico}\" "
                        f"AND group_participants.admin = {TIPI_PARTECIPANTI.get('Partecipante')}")
        risultato = cursore.fetchall()
        if risultato:
            _id, numeriTelefonici = zip(*risultato)
            nomi = numeriTelefonici
            partecipanti = list(map(ContattoDB, _id, numeriTelefonici, nomi))
        else:
            partecipanti = []
        return partecipanti

    @property
    def amministratori(self)->list[Contatto]:
        cursore = self.msgstore.cursor()
        cursore.execute("SELECT contacts._id, contacts.user "
                        "FROM group_participants "
                        "JOIN jid groups "
                        "ON group_participants.gjid = groups.raw_string "
                        "JOIN jid contacts "
                        "ON group_participants.jid = contacts.raw_string "
                        f"WHERE groups.user = \"{self.numeroTelefonico}\" "
                        f"AND group_participants.admin = {TIPI_PARTECIPANTI.get('Amministratore')}")
        risultato = cursore.fetchall()
        if risultato:
            _id, numeriTelefonici = zip(*risultato)
            nomi = numeriTelefonici
            amministratori = list(map(ContattoDB, _id, numeriTelefonici, nomi))
        else:
            amministratori = []
        return amministratori
    
    @property
    def creatore(self)->Contatto:
        cursore = self.msgstore.cursor()
        cursore.execute("SELECT jid._id, jid.user "
                        "FROM jid "
                       f"WHERE jid.user = \"{self.numeroTelefonico[0:12]}\"")
        risultato = cursore.fetchone()
        _id, numeroTelefonico = risultato if risultato is not None else (None, "Non trovato")
        nome = numeroTelefonico
        creatore = ContattoDB(_id, numeroTelefonico, nome)
        return creatore

    @property
    def messaggi(self)->list[Messaggio]:
        cursore = self.msgstore.cursor()
        cursore.execute("SELECT message_view._id, message_view.text_data, message_view.timestamp, message_view.received_timestamp "
                        "FROM message_view "
                        "JOIN chat_view "
                        "ON message_view.chat_row_id = chat_view._id "
                        "JOIN jid "
                        "ON chat_view.raw_string_jid = jid.raw_string "
                        f"WHERE jid._id = {self._id}")
        _id, contenuti, dateInvio, dateRicezione = zip(*cursore.fetchall())
        messaggi = list(map(MessaggioDB, _id, contenuti, dateInvio, dateRicezione))
        return messaggi

class MessaggioDB():
    _id: int
    contenuto: str
    dataInvio: datetime
    dataRicezione: datetime
    msgstore: sqlite3.Connection

    def __init__(self, _id: int, contenuto: str, dataInvio: datetime, dataRicezione: datetime):
        self._id = _id
        self.contenuto = contenuto
        self.dataInvio = dataInvio
        self.dataRicezione = dataRicezione

    @property
    def mittente(self)->Contatto:
        pass

    @property
    def destinatariEffettivi(self)->list[tuple[Contatto, datetime]]:
        pass

    @property
    def lettori(self)->list[tuple[Contatto, datetime]]:
        pass

    @property
    def lettoriMedia(self)->list[tuple[Contatto, datetime]]:
        pass
    