print("Adding tariff validation...")

with open('dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the createTariff function and replace it entirely with a validated version
lines = c.split('\n')
new_lines = []
skip = False
depth = 0
replaced = False

new_func = """    async function createTariff() {
        const propId = document.getElementById("propertyFilter").value;
        if(!propId) { alert("Please select a property first."); return; }
        const structure = document.getElementById("tariffStructure").value;
        const mType = document.getElementById("tariffMeterType").value;
        
        let flat_rate_val = 0;
        let tier_1_limit_val = 0;
        let tier_1_rate_val = 0;
        let tier_2_rate_val = 0;
        let tou_peak_rate_val = 0;
        let tou_offpeak_rate_val = 0;

        if (structure === 'FLAT') {
            if (mType === 'WATER_HOT') {
                let base = parseFloat(document.getElementById("hwBaseRate").value || 0);
                if (isNaN(base)) base = 0;
                let surcharge = parseFloat(document.getElementById("hwSurcharge").value || 227.26);
                if (isNaN(surcharge)) surcharge = 227.26;
                flat_rate_val = base + surcharge;
            } else {
                flat_rate_val = parseFloat(document.getElementById("rateFlat").value || 0);
                if (isNaN(flat_rate_val)) flat_rate_val = 0;
            }
        } else if (structure === 'TIERED') {
            tier_1_limit_val = parseFloat(document.getElementById("tier1Limit").value || 0);
            if (isNaN(tier_1_limit_val)) tier_1_limit_val = 0;
            tier_1_rate_val = parseFloat(document.getElementById("tier1Rate").value || 0);
            if (isNaN(tier_1_rate_val)) tier_1_rate_val = 0;
            tier_2_rate_val = parseFloat(document.getElementById("tier2Rate").value || 0);
            if (isNaN(tier_2_rate_val)) tier_2_rate_val = 0;
        } else if (structure === 'TOU') {
            tou_peak_rate_val = parseFloat(document.getElementById("touPeak").value || 0);
            if (isNaN(tou_peak_rate_val)) tou_peak_rate_val = 0;
            tou_offpeak_rate_val = parseFloat(document.getElementById("touOffpeak").value || 0);
            if (isNaN(tou_offpeak_rate_val)) tou_offpeak_rate_val = 0;
        }

        // VALIDATION 1: Check for zero rates
        if (structure === 'FLAT' && flat_rate_val <= 0) {
            if (mType === 'WATER_HOT') {
                alert("ERROR: Hot water final rate is R0.00.\\n\\nPlease ensure:\\n1. A Cold Water flat rate tariff exists\\n2. The surcharge is entered\\n\\nThe final rate = Cold Water Base + Surcharge");
            } else {
                alert("ERROR: Rate cannot be 0.\\n\\nPlease enter a valid rate for the " + mType + " tariff.");
            }
            return;
        }
        if (structure === 'TIERED' && tier_1_rate_val <= 0 && tier_2_rate_val <= 0) {
            alert("ERROR: Tier 1 and Tier 2 rates cannot both be 0.\\n\\nPlease enter at least one valid rate.");
            return;
        }
        if (structure === 'TOU' && tou_peak_rate_val <= 0 && tou_offpeak_rate_val <= 0) {
            alert("ERROR: Peak and Off-Peak rates cannot both be 0.\\n\\nPlease enter at least one valid rate.");
            return;
        }

        // VALIDATION 2: Check for hot water without cold water
        if (mType === 'WATER_HOT') {
            let coldWaterTariff = allTariffsCache.find(t => (t.meter_type === 'WATER_COLD') && ((t.structure || t.structure_type) === 'FLAT'));
            if(!coldWaterTariff) {
                alert("ERROR: Cannot create Hot Water tariff.\\n\\nPlease create a Cold Water flat rate tariff FIRST.\\nThe hot water rate is calculated as: Cold Water Base Rate + Surcharge.");
                return;
            }
            let cwRate = coldWaterTariff.rate_flat || coldWaterTariff.flat_rate || 0;
            if(cwRate <= 0) {
                alert("ERROR: Cold Water tariff exists but has a rate of R0.00.\\n\\nPlease edit the Cold Water tariff to have a valid rate first.");
                return;
            }
            // Update the base rate display
            document.getElementById("hwBaseRate").value = parseFloat(cwRate).toFixed(2);
            calcHotWater();
            // Recalculate after update
            base = parseFloat(cwRate);
            surcharge = parseFloat(document.getElementById("hwSurcharge").value || 227.26);
            flat_rate_val = base + surcharge;
        }

        const payload = {
            property_id: parseInt(propId),
            name: document.getElementById("tariffName").value,
            meter_type: mType,
            structure_type: structure,
            rate_flat: flat_rate_val,
            tier_1_limit: tier_1_limit_val,
            tier_1_rate: tier_1_rate_val,
            tier_2_rate: tier_2_rate_val,
            tou_peak_rate: tou_peak_rate_val,
            tou_offpeak_rate: tou_offpeak_rate_val
        };
        
        if(!payload.name) {
            alert("Please enter a tariff name.");
            return;
        }
        
        try {
            const url = `/tariffs`;
            const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` }, body: JSON.stringify(payload) });
            const d = await r.json();
            if (!r.ok) throw new Error(extractError(d));
            alert(d.message + "\\n\\nRate: R" + flat_rate_val.toFixed(2));
            // CLEAR FIELDS
            document.getElementById('tariffName').value = '';
            document.getElementById('rateFlat').value = '';
            document.getElementById('tier1Limit').value = '';
            document.getElementById('tier1Rate').value = '';
            document.getElementById('tier2Rate').value = '';
            document.getElementById('touPeak').value = '';
            document.getElementById('touOffpeak').value = '';
            document.getElementById('hwSurcharge').value = '';
            document.getElementById('hwBaseRate').value = '';
            document.getElementById('hwFinalRate').value = '';
            document.getElementById('tariffMeterType').selectedIndex = 0;
            document.getElementById('tariffStructure').selectedIndex = 0;
            toggleTariffFields();
            loadTariffs();
        } catch (e) { alert(`Error calling ${url}: ` + e.message); }
    }"""

for line in lines:
    if not skip and 'function createTariff' in line:
        skip = True
        depth = line.count('{') - line.count('}')
        new_lines.append(new_func)
        replaced = True
        if depth <= 0:
            skip = False
        continue
    if skip:
        depth += line.count('{') - line.count('}')
        if depth <= 0:
            skip = False
        continue
    new_lines.append(line)

if replaced:
    c = '\n'.join(new_lines)
    print("  Replaced createTariff with validated version.")
else:
    print("  WARNING: createTariff not found!")

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nDone! Restart server and test.")
print("\nTest scenarios:")
print("  1. Try create electricity with rate 0 -> should block")
print("  2. Try create hot water without cold water -> should block")
print("  3. Create cold water first -> then hot water -> should work")
print("  4. After creating, fields should clear automatically")