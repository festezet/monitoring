#!/usr/bin/env python3
"""
Script de test pour simuler une charge mémoire
Permet de vérifier la détection de menaces dans System Monitor
"""

import time
import sys

def allocate_memory_gb(gb):
    """Alloue une quantité de mémoire en GB"""
    print(f"🧪 Allocation de {gb} GB de RAM...")

    # Allouer un tableau de bytes
    # 1 GB = 1024^3 bytes
    bytes_per_gb = 1024 * 1024 * 1024

    try:
        # Créer une liste de bytes
        memory_hog = bytearray(int(gb * bytes_per_gb))

        print(f"✅ {gb} GB alloués avec succès")
        print(f"📊 Ouvre http://localhost:8888 dans Chromium pour voir l'alerte")
        print(f"⏰ Maintien de la charge pendant 60 secondes...")
        print(f"💡 Appuie sur Ctrl+C pour arrêter plus tôt")

        # Maintenir l'allocation pendant 60 secondes
        for i in range(60):
            time.sleep(1)
            # Écrire dans la mémoire pour éviter optimisation
            if i % 5 == 0:
                memory_hog[0] = i
                print(f"   ... {60-i} secondes restantes")

        print(f"✅ Test terminé, libération de la mémoire")

    except MemoryError:
        print(f"❌ Impossible d'allouer {gb} GB (pas assez de RAM)")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrompu par l'utilisateur")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            gb = float(sys.argv[1])
        except ValueError:
            print("❌ Usage: python3 test_memory_load.py [GB]")
            print("   Exemple: python3 test_memory_load.py 3")
            sys.exit(1)
    else:
        gb = 3  # Par défaut 3 GB

    print("="*60)
    print("🧪 TEST DE CHARGE MÉMOIRE - System Monitor")
    print("="*60)
    print()
    print(f"⚠️  Ce script va allouer {gb} GB de RAM")
    print(f"📊 RAM système totale : ~13.54 GB")
    print(f"💡 Seuils d'alerte :")
    print(f"   - Processus >2 GB : Alerte orange")
    print(f"   - Processus >4 GB : Risque critique")
    print(f"   - RAM libre <1 GB : DANGER CRASH")
    print()

    # Mode automatique si stdin non interactif
    import sys
    if sys.stdin.isatty():
        input("Appuie sur Entrée pour démarrer le test...")
        print()
    else:
        print("🤖 Mode automatique détecté, démarrage immédiat...")
        print()

    allocate_memory_gb(gb)
