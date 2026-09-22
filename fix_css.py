def fix_css(filename, css_marker):
    print(f"Checking {filename}...")
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    marker_pos = content.find(css_marker)
    style_pos = content.find('<style>')
    
    if marker_pos == -1:
        print(f"  CSS not found. Skipping.")
        return
    if style_pos == -1:
        print(f"  No <style> tag. Skipping.")
        return
    if marker_pos > style_pos:
        print(f"  CSS already inside <style>. OK.")
        return
    
    # CSS is before <style> — move it inside
    css_start = content.rfind('\n', max(0, marker_pos - 500), marker_pos) + 1
    css_end = style_pos
    css_block = content[css_start:css_end]
    
    content = content[:css_start] + content[css_end:]
    new_style_pos = content.find('<style>')
    content = content[:new_style_pos + 7] + '\n' + css_block + '\n' + content[new_style_pos + 7:]
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Fixed! CSS moved inside <style> tag.")

fix_css('dashboard.html', '.smart-meter-card')
fix_css('tenant_portal.html', '.consumption-chart-container')

print("\nDone! Press Ctrl+F5 in your browser to check.")