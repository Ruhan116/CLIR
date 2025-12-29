#!/usr/bin/env python3
"""Check which languages Stanza supports and if Bengali is available."""

import stanza
from stanza.resources.common import list_available_languages

print("Checking Stanza language support...")
print("=" * 60)

try:
    # Get list of available languages
    langs = list_available_languages()
    print(f"\nTotal languages available: {len(langs)}")
    print(f"\nSupported languages:")
    print(sorted(langs))

    # Check if Bengali is in the list
    if 'bn' in langs:
        print("\n✓ Bengali (bn) IS supported!")

        # Try to get resources info for Bengali
        try:
            from stanza.resources.common import get_lang_resources_info
            bn_info = get_lang_resources_info('bn')
            print(f"\nBengali resources available:")
            print(f"  {bn_info}")
        except Exception as e:
            print(f"\n  Could not get Bengali resource details: {e}")
    else:
        print("\n✗ Bengali (bn) is NOT in the supported languages list")

        # Check for alternative codes
        bengali_like = [lang for lang in langs if 'ben' in lang.lower() or 'ban' in lang.lower()]
        if bengali_like:
            print(f"  Similar codes found: {bengali_like}")

except Exception as e:
    print(f"Error checking languages: {e}")
    print("\nTrying alternative method...")

    try:
        # Try to access resources directly
        import stanza.resources.common as resources
        print(f"\nAvailable attributes in resources: {dir(resources)}")
    except Exception as e2:
        print(f"Alternative method also failed: {e2}")