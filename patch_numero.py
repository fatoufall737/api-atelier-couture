p = "app/services/commande_service.py"
s = open(p, encoding="utf-8-sig").read()
ancien = 'numero=f"TEMP-{uuid4().hex}",'
nouveau = 'numero=f"T{uuid4().hex[:12]}",'
assert s.count(ancien) == 1, "ligne numero introuvable"
open(p, "w", encoding="utf-8").write(s.replace(ancien, nouveau))
print("OK : numero provisoire raccourci")
