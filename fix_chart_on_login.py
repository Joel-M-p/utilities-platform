"""
fix_chart_on_login.py
---------------------
Fixes: chart doesn't load on first login, only after refresh.

Two patches to tenant_portal.html:

1. In the page-init block: call loadConsumptionChart() after
   tLoadDashboard() completes (await).

2. In tLogin(): call loadConsumptionChart() after login succeeds.
"""

import os, re, shutil, sys
from datetime import datetime

TARGET = "tenant_portal.html"
BACKUP = TARGET + ".loginchartbak." + datetime.now().strftime("%Y%m%d-%H%M%S")


def main():
    if not os.path.isfile(TARGET):
        print(f"ERROR: {TARGET} not found"); sys.exit(1)

    with open(TARGET, encoding="utf-8") as f:
        src = f.read()

    if "// [loginchart] post-login chart load" in src:
        print("Fix already applied. Nothing to do.")
        sys.exit(0)

    original = src

    # ---- Patch 1: page-init block ----
    # Old:
    #     tLoadDashboard();
    #     tLoadTransactions();
    #     loadConsumptionChart();
    # New:
    #     (async function() {
    #         await tLoadDashboard();
    #         tLoadTransactions();
    #         loadConsumptionChart();
    #     })();
    old_init = (
        "        tLoadDashboard();\n"
        "        tLoadTransactions();\n"
        "        loadConsumptionChart();"
    )
    new_init = (
        "        (async function() {\n"
        "            await tLoadDashboard();\n"
        "            tLoadTransactions();\n"
        "            loadConsumptionChart();\n"
        "        })();"
    )
    if old_init not in src:
        print("ERROR: could not find the page-init block.")
        print("Looking for:")
        print(repr(old_init))
        sys.exit(1)
    src = src.replace(old_init, new_init, 1)
    print("  [ok] Patch 1: page-init now awaits tLoadDashboard() before chart")

    # ---- Patch 2: inside tLogin() after successful login ----
    # We look for the second call to tLoadTransactions() inside tLogin()
    # which currently has:
    #     tLogAction("Tenant Login", ...);
    #     tLoadDashboard();
    #     tLoadTransactions();
    old_login = (
        '            tLogAction("Tenant Login", `Prop ID: ${property_id}, Unit: ${unitNumber} logged in.`);\n'
        '            tLoadDashboard();\n'
        '            tLoadTransactions();'
    )
    new_login = (
        '            tLogAction("Tenant Login", `Prop ID: ${property_id}, Unit: ${unitNumber} logged in.`);\n'
        '            // [loginchart] post-login chart load\n'
        '            await tLoadDashboard();\n'
        '            tLoadTransactions();\n'
        '            loadConsumptionChart();\n'
        '            loadConsumptionComparison();'
    )
    if old_login not in src:
        # Fallback: maybe tLogAction string differs. Try a simpler anchor.
        print("WARNING: exact login block not found, trying broader match...")
        # Match: within tLogin function, the two consecutive calls
        # tLoadDashboard(); \n tLoadTransactions();
        # and add the chart load after.
        pat = re.compile(
            r'(tLogAction\("Tenant Login"[^\n]*\n\s*)'
            r'(tLoadDashboard\(\);\s*\n\s*tLoadTransactions\(\);)',
            re.MULTILINE,
        )
        def repl(m):
            return m.group(1) + "// [loginchart] post-login chart load\n            await " + m.group(2) + "\n            loadConsumptionChart();\n            loadConsumptionComparison();"
        src, n = pat.subn(repl, src, count=1)
        if n == 0:
            print("ERROR: could not patch the login block. Manual fix needed.")
            sys.exit(1)
        print("  [ok] Patch 2 (fallback): login now triggers chart load")
    else:
        src = src.replace(old_login, new_login, 1)
        print("  [ok] Patch 2: login triggers chart load after dashboard ready")

    # ---- Syntax-ish sanity check ----
    if "loadConsumptionChart()" not in src or "[loginchart]" not in src:
        print("ERROR: sanity check failed, restoring.")
        sys.exit(1)

    shutil.copy2(TARGET, BACKUP)
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(src)

    print(f"\nBackup: {BACKUP}")
    print("Done.")
    print()
    print("Now:")
    print("  1. Hard-refresh the tenant portal ONCE (Ctrl+Shift+R)")
    print("  2. Log out")
    print("  3. Log in again")
    print("  4. Chart should appear immediately, no refresh needed")


if __name__ == "__main__":
    main()