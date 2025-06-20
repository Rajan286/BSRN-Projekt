"""
@file peer.py
@brief Definiert die Peer-Klasse, die einen Chat-Teilnehmer modelliert.

Die Klasse Peer kapselt Handle, IP-Adresse und Port eines Chat-Teilnehmers
und stellt Methoden für Vergleich und Adresszugriff bereit.
"""

class Peer:
    """
    @brief Repräsentiert einen Chat-Teilnehmer (Peer) im SLCP-Netzwerk.

    Ein Peer enthält:
    - handle: Der eindeutige Benutzername des Teilnehmers
    - ip: Die IP-Adresse des Teilnehmers
    - port: Der Port, über den der Teilnehmer erreichbar ist
    """
    def __init__(self, handle, ip, port):
        """
        @brief Initialisiert einen Peer.

        @param handle Eindeutiger Benutzername des Peers.
        @param ip IP-Adresse des Peers.
        @param port Portnummer des Peers.
        """
        self.handle = handle  #: Eindeutiger Benutzername des Peers
        self.ip = ip          #: IP-Adresse des Peers
        self.port = port      #: Portnummer des Peers

    def __repr__(self):
        """
        @brief String-Repräsentation eines Peers.

        @return Darstellung in der Form 'handle@ip:port'.
        """
        return f"{self.handle}@{self.ip}:{self.port}"

    def __eq__(self, other):
        """
        @brief Vergleich zweier Peer-Objekte nach ihrem Handle.

        @param other Ein weiteres Objekt.
        @return True, wenn 'other' ein Peer ist und denselben Handle hat.
        """
        return isinstance(other, Peer) and self.handle == other.handle

    def __hash__(self):
        """
        @brief Berechnet den Hash-Wert eines Peers basierend auf dem Handle.

        @return Integer-Hash des Handles.
        """
        return hash(self.handle)

    def get_address(self):
        """
        @brief Liefert ein Tuple aus IP-Adresse und Port für Netzwerkverbindungen.

        @return Tuple (ip, port).
        """
        return (self.ip, self.port)