#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json

EMR_VERSIONS = ['7.x', '6.x', '5.x', '4.x']
BASE_URL = "https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-release-app-versions-{}.html"

def scrape_emr_versions(version_series):
    url = BASE_URL.format(version_series)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    table = soup.find('table')
    rows = table.find_all('tr')
    
    headers = [th.get_text(strip=True) for th in rows[0].find_all('th')][1:]
    versions = [h.replace('emr-', '') for h in headers]
    
    data = {}
    for row in rows[1:]:
        cells = row.find_all('td')
        app_name = cells[0].get_text(strip=True)
        app_versions = [cell.get_text(strip=True).replace(' ', '') for cell in cells[1:]]
        data[app_name] = app_versions
    
    return versions, data

def generate_html(versions, data, version_series):
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EMR VERSION_SERIES Version Differences</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #232f3e;
        }
        .legend {
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
        }
        .legend-item {
            display: inline-block;
            margin-right: 20px;
            padding: 5px 10px;
        }
        .green { background-color: #90EE90; }
        .yellow { background-color: #FFD700; }
        .orange { background-color: #FFA500; }
        .red { background-color: #FF6B6B; }
        .gray { background-color: #E0E0E0; }
        
        table {
            border-collapse: collapse;
            width: 100%;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
            font-size: 12px;
        }
        th {
            background-color: #232f3e;
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        td:first-child, th:first-child {
            text-align: left;
            font-weight: bold;
            position: sticky;
            left: 0;
            background: white;
            z-index: 5;
        }
        th:first-child {
            z-index: 15;
            background-color: #232f3e;
        }
        tr:hover td {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>EMR VERSION_SERIES Application Version Differences</h1>
    
    <div class="legend">
        <strong>Legend:</strong>
        <span class="legend-item green">No Change</span>
        <span class="legend-item yellow">Patch Bump (0.0.x)</span>
        <span class="legend-item orange">Minor Bump (0.x.0)</span>
        <span class="legend-item red">Major Bump (x.0.0)</span>
        <span class="legend-item gray">Not Available</span>
    </div>

    <div style="overflow-x: auto;">
        <table id="versionTable"></table>
    </div>

    <script>
        const data = DATA_PLACEHOLDER;
        const versions = VERSIONS_PLACEHOLDER;

        function parseVersion(v) {
            if (v === "-") return null;
            const match = v.match(/(\\d+)\\.(\\d+)\\.(\\d+)/);
            return match ? [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])] : null;
        }

        function compareVersions(curr, prev) {
            if (!curr || !prev) return curr === prev ? "green" : "gray";
            if (curr[0] !== prev[0]) return "red";
            if (curr[1] !== prev[1]) return "orange";
            if (curr[2] !== prev[2]) return "yellow";
            return "green";
        }

        function getColor(app, idx) {
            const curr = data[app][idx];
            if (idx === data[app].length - 1) return "";
            const prev = data[app][idx + 1];
            
            if (curr === "-" || prev === "-") return curr === prev ? "gray" : "gray";
            if (curr === prev) return "green";
            
            const currVer = parseVersion(curr);
            const prevVer = parseVersion(prev);
            return compareVersions(currVer, prevVer);
        }

        const table = document.getElementById("versionTable");
        let html = "<thead><tr><th>Application</th>";
        versions.forEach(v => html += `<th>emr-${v}</th>`);
        html += "</tr></thead><tbody>";

        Object.keys(data).forEach(app => {
            html += `<tr><td>${app}</td>`;
            data[app].forEach((ver, idx) => {
                const color = getColor(app, idx);
                html += `<td class="${color}">${ver}</td>`;
            });
            html += "</tr>";
        });

        html += "</tbody>";
        table.innerHTML = html;
    </script>
</body>
</html>'''
    
    html = html_template.replace('DATA_PLACEHOLDER', json.dumps(data))
    html = html.replace('VERSIONS_PLACEHOLDER', json.dumps(versions))
    html = html.replace('VERSION_SERIES', version_series)
    
    return html

if __name__ == "__main__":
    for version_series in EMR_VERSIONS:
        print(f"\nFetching EMR {version_series} data...")
        try:
            versions, data = scrape_emr_versions(version_series)
            print(f"Found {len(versions)} EMR versions and {len(data)} applications")
            
            html = generate_html(versions, data, version_series)
            
            output_file = f"emr-{version_series}.html"
            with open(output_file, 'w') as f:
                f.write(html)
            
            print(f"Generated {output_file}")
        except Exception as e:
            print(f"Error processing EMR {version_series}: {e}")
