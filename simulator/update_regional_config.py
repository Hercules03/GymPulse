#!/usr/bin/env python3
"""
Update store configuration to use regional prefixes (HK, KL, NT)
"""
import json

def update_regional_config():
    """Update branch configuration with regional organization"""

    # Regional mapping
    regional_mapping = {
        # Hong Kong Island (HK)
        "hk-central-caine": {
            "new_id": "hk-central-caine",
            "region": "HK",
            "name": "Central Caine Road (Flagship)"
        },
        "hk-causeway-hennessy": {
            "new_id": "hk-causeway-hennessy",
            "region": "HK",
            "name": "Causeway Bay Hennessy Road"
        },
        "hk-quarrybay-westlands": {
            "new_id": "hk-quarrybay-westlands",
            "region": "HK",
            "name": "Quarry Bay Westlands Centre"
        },

        # Kowloon (KL)
        "hk-mongkok-nathan": {
            "new_id": "kl-mongkok-nathan",
            "region": "KL",
            "name": "Mongkok Nathan Road"
        },
        "hk-tsimshatsui-ashley": {
            "new_id": "kl-tsimshatsui-ashley",
            "region": "KL",
            "name": "Tsim Sha Tsui Ashley Road"
        },
        "hk-jordan-nathan": {
            "new_id": "kl-jordan-nathan",
            "region": "KL",
            "name": "Jordan Nathan Road"
        },
        "hk-taikok-ivy": {
            "new_id": "kl-taikok-ivy",
            "region": "KL",
            "name": "Tai Kok Tsui Ivy Street"
        },

        # New Territories (NT)
        "hk-shatin-fun": {
            "new_id": "nt-shatin-fun",
            "region": "NT",
            "name": "Shatin Fun City"
        },
        "hk-maonshan-lee": {
            "new_id": "nt-maonshan-lee",
            "region": "NT",
            "name": "Ma On Shan Lee On"
        },
        "hk-tsuenwan-lik": {
            "new_id": "nt-tsuenwan-lik",
            "region": "NT",
            "name": "Tsuen Wan Lik Sang Plaza"
        },
        "hk-tinshui-tin": {
            "new_id": "nt-tinshui-tin",
            "region": "NT",
            "name": "Tin Shui Wai Tin Yiu Plaza"
        },
        "hk-fanling-green": {
            "new_id": "nt-fanling-green",
            "region": "NT",
            "name": "Fanling Green Code Plaza"
        }
    }

    print("🔄 Updating branch configuration with regional organization...")

    # Read current configuration
    with open('config/realistic_247_stores.json', 'r') as f:
        config = json.load(f)

    # Update branches
    updated_branches = []
    for branch in config['branches']:
        old_id = branch['id']

        if old_id in regional_mapping:
            mapping = regional_mapping[old_id]

            # Update branch with regional info
            branch['id'] = mapping['new_id']
            branch['name'] = mapping['name']
            branch['region'] = mapping['region']

            print(f"✅ {old_id} → {mapping['new_id']} ({mapping['region']})")
        else:
            print(f"⚠️  No mapping found for: {old_id}")

        updated_branches.append(branch)

    config['branches'] = updated_branches

    # Save updated configuration
    with open('config/realistic_247_stores.json', 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\n📊 Regional Summary:")
    regions = {}
    for branch in updated_branches:
        region = branch.get('region', 'Unknown')
        if region not in regions:
            regions[region] = []
        regions[region].append(branch['name'])

    for region, stores in regions.items():
        print(f"   {region}: {len(stores)} stores")
        for store in stores:
            print(f"      - {store}")

    print(f"\n✅ Configuration updated! Now regenerate machines.json...")
    return True

if __name__ == "__main__":
    update_regional_config()