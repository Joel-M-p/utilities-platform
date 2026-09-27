print("Fixing tariff form clearing...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the loadTariffs() call inside createTariff function (after tariffResult)
# and add clearing code before it
tariff_pos = c.find('tariffResult')
if tariff_pos != -1:
    load_pos = c.find('loadTariffs();', tariff_pos)
    if load_pos != -1:
        # Check if clearing is already there
        before = c[load_pos-300:load_pos]
        if "tariffName').value = ''" not in before:
            clearing = "document.getElementById('tariffName').value = ''; document.getElementById('rateFlat').value = ''; document.getElementById('tier1Limit').value = ''; document.getElementById('tier1Rate').value = ''; document.getElementById('tier2Rate').value = ''; document.getElementById('touPeak').value = ''; document.getElementById('touOffpeak').value = ''; document.getElementById('tariffMeterType').selectedIndex = 0; document.getElementById('tariffStructure').selectedIndex = 0; toggleTariffFields(); "
            c = c[:load_pos] + clearing + c[load_pos:]
            print("  Added clearing to createTariff function.")
        else:
            print("  Tariff clearing already exists.")
    else:
        print("  Could not find loadTariffs() after tariffResult.")
else:
    print("  Could not find tariffResult.")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Test: Create a tariff → fields should clear after saving.")