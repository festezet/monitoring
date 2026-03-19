#!/usr/bin/env python3
"""
System Monitoring - Mode CLI
Consultation des metriques systeme depuis le terminal.

Usage:
    python3 cli.py status
    python3 cli.py cpu
    python3 cli.py memory
    python3 cli.py gpu
    python3 cli.py disk
    python3 cli.py processes [--limit N]
    python3 cli.py threats
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from main import (
    get_cpu_stats, get_memory_stats, get_gpu_stats,
    get_disk_stats, get_top_processes, detect_memory_threats,
)


def cmd_status(args):
    """Full system status overview."""
    cpu = get_cpu_stats()
    mem = get_memory_stats()
    gpu = get_gpu_stats()
    threats = detect_memory_threats()

    print("=== System Status ===")
    print(f"CPU    : {cpu['percent_avg']:.1f}% ({cpu['core_count']} cores @ {cpu['frequency_mhz']:.0f} MHz)")
    print(f"RAM    : {mem['used_gb']:.1f}/{mem['total_gb']:.1f} GB ({mem['percent']:.0f}%)")
    print(f"Swap   : {mem['swap_used_gb']:.1f}/{mem['swap_total_gb']:.1f} GB ({mem['swap_percent']:.0f}%)")

    if gpu.get('available'):
        print(f"GPU    : {gpu['name']} - {gpu['utilization_percent']}% util")
        print(f"VRAM   : {gpu['memory_used_gb']:.1f}/{gpu['memory_total_gb']:.1f} GB")
        print(f"Temp   : {gpu['temperature_c']}C | Power: {gpu['power_usage_w']:.0f}/{gpu['power_limit_w']:.0f} W")
    else:
        print("GPU    : non disponible")

    if threats['critical_alert']:
        print(f"\n*** ALERTE RAM CRITIQUE: {threats['available_gb']:.2f} GB disponible ***")
        for t in threats['threats'][:3]:
            print(f"  - {t['name']} (PID {t['pid']}): {t['memory_gb']:.1f} GB [{t['risk_level']}]")


def cmd_cpu(args):
    """CPU details."""
    cpu = get_cpu_stats()
    print(f"CPU moyen  : {cpu['percent_avg']:.1f}%")
    print(f"Cores      : {cpu['core_count']}")
    print(f"Frequence  : {cpu['frequency_mhz']:.0f} / {cpu['frequency_max_mhz']:.0f} MHz")
    print(f"\nPar core :")
    for i, pct in enumerate(cpu['percent_per_core']):
        bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
        print(f"  Core {i:2d}: [{bar}] {pct:5.1f}%")


def cmd_memory(args):
    """Memory details."""
    mem = get_memory_stats()
    print("=== RAM ===")
    print(f"Total       : {mem['total_gb']:.2f} GB")
    print(f"Utilise     : {mem['used_gb']:.2f} GB ({mem['percent']:.0f}%)")
    print(f"Disponible  : {mem['available_gb']:.2f} GB")
    print(f"\n=== Swap ===")
    print(f"Total       : {mem['swap_total_gb']:.2f} GB")
    print(f"Utilise     : {mem['swap_used_gb']:.2f} GB ({mem['swap_percent']:.0f}%)")


def cmd_gpu(args):
    """GPU details."""
    gpu = get_gpu_stats()
    if not gpu.get('available'):
        print("GPU non disponible.")
        return

    print(f"GPU         : {gpu['name']}")
    print(f"Utilisation : {gpu['utilization_percent']}%")
    print(f"VRAM        : {gpu['memory_used_gb']:.1f}/{gpu['memory_total_gb']:.1f} GB ({gpu['memory_utilization_percent']}%)")
    print(f"Temperature : {gpu['temperature_c']}C")
    print(f"Power       : {gpu['power_usage_w']:.0f}/{gpu['power_limit_w']:.0f} W")

    procs = gpu.get('processes', [])
    if procs:
        print(f"\nProcessus GPU :")
        for p in procs:
            print(f"  PID {p['pid']:>6} {p['name']:<25} {p['vram_mb']:.0f} MB VRAM")


def cmd_disk(args):
    """Disk usage."""
    disk = get_disk_stats()
    parts = disk.get('partitions', [])

    print(f"{'Device':<20} {'Mount':<20} {'Type':<8} {'Used':>8} {'Total':>8} {'%':>5}")
    print("-" * 73)
    for p in parts:
        print(f"{p['device']:<20} {p['mountpoint']:<20} {p['fstype']:<8} "
              f"{p['used_gb']:>7.1f}G {p['total_gb']:>7.1f}G {p['percent']:>4.0f}%")


def cmd_processes(args):
    """Top processes by CPU usage."""
    procs = get_top_processes(args.limit)

    print(f"{'PID':>7} {'Nom':<25} {'CPU%':>6} {'RAM%':>6} {'RAM MB':>8}")
    print("-" * 56)
    for p in procs:
        print(f"{p['pid']:>7} {p['name']:<25} {p['cpu_percent']:>5.1f}% {p['memory_percent']:>5.1f}% {p['memory_mb']:>7.1f}")


def cmd_threats(args):
    """Memory threat detection."""
    threats = detect_memory_threats()

    if threats['critical_alert']:
        print(f"*** ALERTE CRITIQUE: seulement {threats['available_gb']:.2f} GB disponible (seuil: {threats['threshold_gb']} GB) ***")
    else:
        print(f"RAM disponible: {threats['available_gb']:.2f} GB (seuil critique: {threats['threshold_gb']} GB)")

    if threats['threats']:
        print(f"\nProcessus menacants ({threats['threat_count']}) :")
        for t in threats['threats']:
            level = "CRITIQUE" if t['risk_level'] == 'critical' else "ELEVE"
            print(f"  [{level}] PID {t['pid']:>6} {t['name']:<20} {t['memory_gb']:.1f} GB ({t['memory_percent']:.1f}%)")
    else:
        print("Aucune menace detectee.")


def main():
    parser = argparse.ArgumentParser(
        description="System Monitoring - CLI",
        prog="cli.py"
    )
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('status', help='Vue complete du systeme')
    sub.add_parser('cpu', help='Details CPU')
    sub.add_parser('memory', help='Details memoire')
    sub.add_parser('gpu', help='Details GPU')
    sub.add_parser('disk', help='Usage disques')

    p_proc = sub.add_parser('processes', help='Top processus')
    p_proc.add_argument('--limit', type=int, default=10, help='Nombre de processus (defaut: 10)')

    sub.add_parser('threats', help='Detection menaces memoire')

    args = parser.parse_args()
    commands = {
        'status': cmd_status,
        'cpu': cmd_cpu,
        'memory': cmd_memory,
        'gpu': cmd_gpu,
        'disk': cmd_disk,
        'processes': cmd_processes,
        'threats': cmd_threats,
    }
    commands[args.command](args)


if __name__ == '__main__':
    main()
