import socket
from DiscoveryService import DiscoveryService
from User import User  
 

# Beispiel-User
User1=User("bileya","192.168.1.11",6000)
User2=User("yasmin","192.168.1.1",6001)

# Discovery-Dienst starten
discovery_service = DiscoveryService([User1,User2])
discovery_service.start()


