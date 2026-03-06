#!/usr/bin/env python3
"""
Test RÉEL de charge mémoire - Force écriture en RAM
"""
import time
import numpy as np

def eat_memory_gb(gb, duration=60):
    """Alloue et ÉCRIT vraiment en RAM"""
    print(f"🧪 Allocation RÉELLE de {gb} GB en RAM...")

    # Créer un tableau numpy et l'initialiser (force RAM)
    # 1 GB = 1024^3 bytes / 8 (float64) éléments
    elements = int((gb * 1024**3) / 8)

    print(f"📝 Création tableau numpy de {elements:,} éléments...")
    memory_hog = np.ones(elements, dtype=np.float64)

    print(f"✅ {gb} GB RÉELLEMENT alloués en RAM")
    print(f"📊 REGARDE CHROMIUM http://localhost:8888 MAINTENANT!")
    print(f"⏰ Maintien pendant {duration} secondes...")

    for i in range(duration):
        # Écrire dans la mémoire pour garantir qu'elle reste en RAM
        if i % 5 == 0:
            memory_hog[i % 1000] = i
            print(f"   ... {duration-i} sec restantes (RAM: {gb} GB actifs)")
        time.sleep(1)

    print(f"✅ Test terminé, libération mémoire")
    del memory_hog

if __name__ == "__main__":
    import sys
    gb = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0

    print("="*60)
    print("🧪 TEST CHARGE MÉMOIRE RÉELLE - NumPy")
    print("="*60)
    print(f"⚠️  Allocation RÉELLE de {gb} GB en RAM")
    print()

    eat_memory_gb(gb, duration=60)
