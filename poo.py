class Poule(object):
    def __init__(self):
        self._race = ""
        self._sexe = ""
        self._estcouveuse = False

    @property
    def race(self):
        return self._race

    @race.setter
    def race(self, param):
        self._race = param

    @property
    def sexe(self):
        return self._sexe

    @sexe.setter
    def sexe(self, param):
        if param not in ("M", "F"):
            raise ValueError("Le sexe doit être 'M' ou 'F'")
        self._sexe = param

    @property
    def estcouveuse(self):
        return self._estcouveuse
    @estcouveuse.setter
    def estcouveuse(self, param):
        self._estcouveuse = param

# brahma = Poule()
# brahma.race = "brahma"
# brahma.sexe = "F"
# brahma.estcouveuse = False

# print(brahma.sexe)

class Maison(object):
    def __init__(self, location="", superficie=0, estPrete=False):
        self.location = location
        self.superficie = superficie
        self.estPrete = estPrete

    def _location(self):
        return self.location

    def _superficie(self):
        return self.superficie

    def _estPrete(self):
        return self.estPrete

# villa = Maison("dakar", 123, True)
# print(villa.location, villa.superficie, villa.estPrete)
# print(villa._estPrete())

# class Citron():
#     couleur = "verte"

# inst=Citron()
# inst.bve = "red"
# print(inst.bve)

#Exo7:
class Employe(object):
    def __init__(self, nom, salaire_base):
        self.nom = nom
        self.salaire_base = salaire_base

    def calculer_salaire(self):
        return float(self.salaire_base)

    def afficher(self):
        return print(f'salaire de base de {self.nom} : ',self.salaire_base)

class EmployePleinTemps(Employe):
    def __init__(self, nom, salaire_base, prime):

        super().__init__(nom, salaire_base)
        self.prime = prime

    def calculer_salaire(self):
        return float(self.salaire_base + self.prime)

class Cadre(EmployePleinTemps):
    def __init__(self, nom, salaire_base, prime, indemnite):

        EmployePleinTemps.__init__(self, nom, salaire_base, prime)
        self.indemnite = indemnite

    def calculer_salaire(self):
       return self.salaire_base + self.prime + self.indemnite


#Test
john = Employe("john", 123, )
john.afficher()

zeynab = EmployePleinTemps("zeynab", 324, 190 )
zeynab.afficher()

Ansata = Cadre("Ansata", 1000, 200, 432 )
Ansata.afficher()
