#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FirewallSpec — generation centralisee des commandes pare-feu OS.

Ce module convertit les regles abstraites declarees dans le DSL .jenga
(FirewallRule, networkenabled, ...) en commandes natives pour chaque
plateforme :

  - Windows  : netsh advfirewall firewall add/delete rule
  - macOS    : /usr/libexec/ApplicationFirewall/socketfilterfw --add/--remove
  - Linux    : ufw allow / firewall-cmd / iptables (detection auto runtime)

Les builders d'installer (MSI WiX 3, WiX 4, Inno Setup, PKG macOS, DEB) appellent
ces helpers pour generer le bon snippet sans dupliquer la logique de mapping
(direction, action, protocole, ports, profils).

Tous les helpers retournent des chaines de commandes shell pretes a embarquer
dans les scripts d'installeur. Aucune commande n'est executee ici — c'est le
roi du build qui decide ou (postinstall script, [Run] Inno, CustomAction MSI).

Reference : cas Pong PC<->Android LAN [[pong_firewall_lan_fix]].
"""
from __future__ import annotations
from typing import List, Optional, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from .Api import FirewallRule, Project


# ─────────────────────────────────────────────────────────────────────────────
# Helpers communs
# ─────────────────────────────────────────────────────────────────────────────

def DefaultRuleName(project_name: str) -> str:
    """Nom de regle utilise quand l'user ne le specifie pas."""
    return f"{project_name} (Network)"


def ResolveRules(project: "Project") -> List["FirewallRule"]:
    """
    Retourne la liste de regles a appliquer pour ce projet.

      - Si networkEnabled est False et aucune regle declaree -> [] (rien a faire)
      - Si firewallRules contient des regles -> celles-ci (l'user a choisi)
      - Si networkEnabled est True et aucune regle -> [regle par defaut]
        (in/allow/any/any sur tous profils)
    """
    from .Api import FirewallRule  # import local pour eviter cycle

    if project.firewallRules:
        # L'user a declare au moins une regle -> on respecte son choix
        return list(project.firewallRules)
    if not project.networkEnabled:
        return []
    # Defaut : autorise tout entrant sur l'exe, tous profils
    return [FirewallRule()]


def _ResolveRuleName(rule: "FirewallRule", app_name: str) -> str:
    return rule.name if rule.name else DefaultRuleName(app_name)


def _ProfileFlag(profiles: List[str]) -> str:
    """netsh : convertit ["private","public"] -> "private,public" ; ["any"] -> "any" """
    if not profiles or "any" in [p.lower() for p in profiles]:
        return "any"
    # netsh accepte une liste separee par virgules
    return ",".join(sorted({p.lower() for p in profiles
                            if p.lower() in ("domain", "private", "public")}))


# ─────────────────────────────────────────────────────────────────────────────
# Windows — netsh advfirewall
# ─────────────────────────────────────────────────────────────────────────────
# Format des commandes pour Windows. Compatible WiX 3 (<Product>), WiX 4
# (<Package>) et Inno Setup. La commande netsh est livree nativement avec
# Windows depuis XP — pas de dependance externe.
#
# Documentation : https://learn.microsoft.com/en-us/windows/win32/wfas/cmdadvfirewall

def BuildNetshAddCommands(project: "Project",
                          exe_path_placeholder: str) -> List[str]:
    """
    Genere les commandes 'netsh advfirewall firewall add rule' a executer
    apres install.

    exe_path_placeholder : pour MSI on passe '[#ExeFile]' (substitue par MSI au
                           runtime), pour Inno on passe '{app}\\<exe>.exe'.
    Retourne une liste (potentiellement multiple si direction="both" ou si
    plusieurs regles declarees).
    """
    app_name = project.targetName or project.name
    cmds: List[str] = []
    for rule in ResolveRules(project):
        if rule.action == "block":
            action = "block"
        else:
            action = "allow"
        program = rule.programOverride or exe_path_placeholder
        rule_name = _ResolveRuleName(rule, app_name)
        profile_flag = _ProfileFlag(rule.profiles)

        # netsh accepte protocol=any|tcp|udp en lowercase. Pour "any", on omet
        # le flag (sinon certaines anciennes versions de netsh rejettent).
        protocol_flag = "" if rule.protocol == "any" else f"protocol={rule.protocol}"

        # Ports : si fournis, on les passe en localport. netsh supporte
        # "7777", "7777,8000", "8000-8100". On joint avec virgule.
        port_flag = ""
        if rule.ports:
            port_flag = f"localport={','.join(rule.ports)}"

        # direction="both" -> on genere 2 commandes (in + out)
        if rule.direction == "both":
            directions = ["in", "out"]
        else:
            directions = [rule.direction]

        for d in directions:
            # netsh deduplique sur le nom -> pour direction=both on suffixe.
            full_name = (rule_name + " (out)") if (rule.direction == "both" and d == "out") else rule_name
            parts = [
                "netsh advfirewall firewall add rule",
                f'name="{full_name}"',
                f"dir={d}",
                f"action={action}",
                f'program="{program}"',
                "enable=yes",
                f"profile={profile_flag}",
            ]
            if protocol_flag:
                parts.append(protocol_flag)
            if port_flag:
                parts.append(port_flag)
            cmds.append(" ".join(parts))
    return cmds


def BuildNetshDeleteCommands(project: "Project") -> List[str]:
    """Commandes 'netsh advfirewall firewall delete rule' pour l'uninstall."""
    app_name = project.targetName or project.name
    cmds: List[str] = []
    for rule in ResolveRules(project):
        rule_name = _ResolveRuleName(rule, app_name)
        if rule.direction == "both":
            for suffix in ("", " (out)"):
                cmds.append(
                    f'netsh advfirewall firewall delete rule name="{rule_name}{suffix}"'
                )
        else:
            cmds.append(f'netsh advfirewall firewall delete rule name="{rule_name}"')
    return cmds


# ─────────────────────────────────────────────────────────────────────────────
# macOS — Application Firewall (socketfilterfw)
# ─────────────────────────────────────────────────────────────────────────────
# Sur macOS, le pare-feu applicatif est /usr/libexec/ApplicationFirewall/
# socketfilterfw. Il fonctionne PAR APPLICATION (pas par port) — c'est l'OS
# qui ouvre les sockets necessaires une fois l'app autorisee.
#
# Les hooks sont generes dans le postinstall script du .pkg.

def BuildSocketfilterfwAddScript(project: "Project",
                                 app_path_placeholder: str = "$2") -> List[str]:
    """
    Genere des lignes shell sh-compatible pour ajouter l'app au firewall macOS.

    app_path_placeholder : par defaut '$2' qui est la convention pkgbuild
                           (destination de l'installation). Le builder peut
                           passer un chemin absolu specifique.
    """
    sff = "/usr/libexec/ApplicationFirewall/socketfilterfw"
    if not project.networkEnabled and not project.firewallRules:
        return []
    # On utilise le binaire de l'app (path du .app/Contents/MacOS/<exe> ou du
    # .app bundle directement — socketfilterfw accepte les deux).
    app_name = project.targetName or project.name
    target = f'{app_path_placeholder}/{app_name}'  # postinstall : $2 = install loc
    return [
        "# Autorise l'application dans le pare-feu macOS (sans toucher au stealth mode).",
        f'if [ -x "{sff}" ]; then',
        f'  "{sff}" --add "{target}" >/dev/null 2>&1 || true',
        f'  "{sff}" --unblockapp "{target}" >/dev/null 2>&1 || true',
        "fi",
    ]


def BuildSocketfilterfwRemoveScript(project: "Project",
                                    app_path_placeholder: str = "$2") -> List[str]:
    """Lignes shell pour retirer l'app du firewall (uninstall script .pkg)."""
    sff = "/usr/libexec/ApplicationFirewall/socketfilterfw"
    if not project.networkEnabled and not project.firewallRules:
        return []
    app_name = project.targetName or project.name
    target = f'{app_path_placeholder}/{app_name}'
    return [
        f'if [ -x "{sff}" ]; then',
        f'  "{sff}" --remove "{target}" >/dev/null 2>&1 || true',
        "fi",
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Linux — ufw / firewall-cmd / iptables
# ─────────────────────────────────────────────────────────────────────────────
# Linux n'a pas de "firewall applicatif" universel. La strategie est de
# detecter au moment de l'install quel outil est disponible et l'utiliser :
#
#   1. ufw (Ubuntu/Debian moderne)
#   2. firewall-cmd (Fedora/RHEL/CentOS, firewalld)
#   3. iptables (fallback toute distrib)
#
# Si aucun n'est dispo OU si l'utilisateur n'est pas root, on logue et on
# continue (l'app peut quand meme tourner — c'est juste que le port ne sera
# pas ouvert par defaut).

def BuildLinuxFirewallAddScript(project: "Project") -> List[str]:
    """
    Genere un script sh complet a placer dans DEBIAN/postinst. Detecte
    automatiquement l'outil de firewall disponible. Le script doit etre rendu
    executable (chmod +x) par le builder.

    Convention DEB : DEBIAN/postinst recoit en arg "configure" lors d'un
    install propre. On ne fait rien sur "abort-upgrade" / "abort-remove".
    """
    rules = ResolveRules(project)
    if not rules:
        return []

    lines: List[str] = [
        "#!/bin/sh",
        "# postinst genere par Jenga — ouvre les ports reseau requis par l'app.",
        "set -e",
        "",
        'case "$1" in',
        "  configure)",
        "    ;;",
        "  *)",
        "    exit 0",
        "    ;;",
        "esac",
        "",
    ]

    # Collecte des ports a ouvrir. Sur Linux on raisonne en ports/protocoles
    # (pas en chemin d'exe), donc on agrege.
    port_rules: List[tuple] = []  # (port, protocol)
    has_any_port = False
    for rule in rules:
        if rule.direction == "out":
            continue  # ufw/iptables defaut autorise sortant
        if not rule.ports:
            has_any_port = True
            continue
        for p in rule.ports:
            proto = rule.protocol if rule.protocol in ("tcp", "udp") else "tcp"
            port_rules.append((p, proto))
            if rule.protocol == "any":
                port_rules.append((p, "udp"))  # any -> tcp ET udp

    if has_any_port and not port_rules:
        # Aucun port specifique -> on ne touche pas au firewall systeme.
        # L'admin reseau decidera. On logue juste un message d'info.
        lines += [
            'echo "Jenga: app installed without specific ports — firewall not modified." >&2',
            "exit 0",
            "",
        ]
        return lines

    # Detection runtime + application des regles.
    lines += [
        "# Detection automatique du gestionnaire de firewall present.",
        "if command -v ufw >/dev/null 2>&1; then",
        "  FW=ufw",
        "elif command -v firewall-cmd >/dev/null 2>&1; then",
        "  FW=firewalld",
        "elif command -v iptables >/dev/null 2>&1; then",
        "  FW=iptables",
        "else",
        '  echo "Jenga: aucun firewall detecte (ufw/firewalld/iptables) — skip." >&2',
        "  exit 0",
        "fi",
        "",
    ]

    # Bloc ufw
    lines += ['if [ "$FW" = "ufw" ]; then']
    for port, proto in port_rules:
        lines.append(f"  ufw allow {port}/{proto} >/dev/null 2>&1 || true")
    lines += ["fi", ""]

    # Bloc firewalld
    lines += ['if [ "$FW" = "firewalld" ]; then']
    for port, proto in port_rules:
        lines.append(f"  firewall-cmd --permanent --add-port={port}/{proto} >/dev/null 2>&1 || true")
    lines += [
        "  firewall-cmd --reload >/dev/null 2>&1 || true",
        "fi",
        "",
    ]

    # Bloc iptables (fallback, regle non persistante par defaut — on tente
    # iptables-save si dispo pour la persistance)
    lines += ['if [ "$FW" = "iptables" ]; then']
    for port, proto in port_rules:
        lines.append(
            f"  iptables -A INPUT -p {proto} --dport {port} -j ACCEPT >/dev/null 2>&1 || true"
        )
    lines += [
        "  if command -v iptables-save >/dev/null 2>&1 && [ -d /etc/iptables ]; then",
        "    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true",
        "  fi",
        "fi",
        "",
        "exit 0",
        "",
    ]
    return lines


def BuildLinuxFirewallRemoveScript(project: "Project") -> List[str]:
    """Genere DEBIAN/postrm — retire les regles a la desinstallation."""
    rules = ResolveRules(project)
    if not rules:
        return []

    port_rules: List[tuple] = []
    for rule in rules:
        if rule.direction == "out" or not rule.ports:
            continue
        for p in rule.ports:
            proto = rule.protocol if rule.protocol in ("tcp", "udp") else "tcp"
            port_rules.append((p, proto))
            if rule.protocol == "any":
                port_rules.append((p, "udp"))

    if not port_rules:
        return []

    lines: List[str] = [
        "#!/bin/sh",
        "# postrm genere par Jenga — retire les regles firewall ajoutees a l'install.",
        "set -e",
        "",
        'case "$1" in',
        "  remove|purge)",
        "    ;;",
        "  *)",
        "    exit 0",
        "    ;;",
        "esac",
        "",
        "if command -v ufw >/dev/null 2>&1; then",
    ]
    for port, proto in port_rules:
        lines.append(f"  ufw delete allow {port}/{proto} >/dev/null 2>&1 || true")
    lines += [
        "elif command -v firewall-cmd >/dev/null 2>&1; then",
    ]
    for port, proto in port_rules:
        lines.append(f"  firewall-cmd --permanent --remove-port={port}/{proto} >/dev/null 2>&1 || true")
    lines += [
        "  firewall-cmd --reload >/dev/null 2>&1 || true",
        "elif command -v iptables >/dev/null 2>&1; then",
    ]
    for port, proto in port_rules:
        lines.append(
            f"  iptables -D INPUT -p {proto} --dport {port} -j ACCEPT >/dev/null 2>&1 || true"
        )
    lines += [
        "  if command -v iptables-save >/dev/null 2>&1 && [ -d /etc/iptables ]; then",
        "    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true",
        "  fi",
        "fi",
        "",
        "exit 0",
        "",
    ]
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# Android — auto-injection des uses-permission
# ─────────────────────────────────────────────────────────────────────────────

def ResolveAndroidNetworkPermissions(project: "Project") -> List[str]:
    """
    Retourne la liste de permissions Android a ajouter automatiquement quand
    networkEnabled est True. Le builder Android fusionne cela avec les
    permissions explicites de project.androidPermissions (sans doublon).
    """
    if not project.networkEnabled and not project.firewallRules:
        return []
    return [
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE",
        "android.permission.ACCESS_WIFI_STATE",
    ]


# ─────────────────────────────────────────────────────────────────────────────
# HarmonyOS — auto-injection des requestPermissions (module.json5)
# ─────────────────────────────────────────────────────────────────────────────

def ResolveHarmonyNetworkPermissions(project: "Project") -> List[str]:
    """
    Retourne la liste des permissions HarmonyOS (ohos.permission.*) a injecter
    dans module.json5 > requestPermissions quand networkEnabled est True.

    Le builder HarmonyOS fusionne cela avec les permissions explicites de
    project.harmonyPermissions (sans doublon). Sur HarmonyOS, sans
    ohos.permission.INTERNET l'app ne peut pas ouvrir de socket -> echec LAN.
    """
    if not project.networkEnabled and not project.firewallRules:
        return []
    return [
        "ohos.permission.INTERNET",
        "ohos.permission.GET_NETWORK_INFO",
        "ohos.permission.GET_WIFI_INFO",
    ]


# ─────────────────────────────────────────────────────────────────────────────
# iOS — Info.plist network keys
# ─────────────────────────────────────────────────────────────────────────────

def BuildIosInfoPlistNetworkKeys(project: "Project") -> dict:
    """
    Retourne le sous-dictionnaire a fusionner dans Info.plist pour les
    permissions reseau iOS.

    Cles produites (selon ce que le projet declare) :
      - NSLocalNetworkUsageDescription : si networkEnabled OU bonjourServices
        non-vide. Defaut : "{AppName} a besoin d'acceder au reseau local."
      - NSBonjourServices : si bonjourServices declares
      - NSAppTransportSecurity : si allowArbitraryLoads = True
    """
    keys: dict = {}
    has_net = (project.networkEnabled or
               bool(project.firewallRules) or
               bool(project.bonjourServices))
    if has_net:
        desc = project.networkUsageDescription
        if not desc:
            app_name = project.targetName or project.name
            desc = f"{app_name} a besoin d'acceder au reseau local pour fonctionner."
        keys["NSLocalNetworkUsageDescription"] = desc
    if project.bonjourServices:
        keys["NSBonjourServices"] = list(project.bonjourServices)
    if project.allowArbitraryLoads:
        keys["NSAppTransportSecurity"] = {
            "NSAllowsArbitraryLoads": True,
        }
    return keys
