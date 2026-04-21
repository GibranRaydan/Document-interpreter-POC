from django.db import migrations

EXTRACTOR_PROMPT = (
    "You are a structured data extraction engine for land record documents. "
    "Extract all relevant fields and return ONLY a valid JSON object. "
    "Do not include any explanation or markdown. Return raw JSON only.\n\n"
    "IMPORTANT RULES FOR PARTIES:\n"
    "- Separate parties into two lists: individual_parties (people) and firm_parties (companies, banks, entities).\n"
    "- The only valid party_type values are GRANTOR and GRANTEE. Never use BUYER, SELLER, "
    "TRUSTEE, LENDER, PURCHASER, or any other term.\n"
    "- Use GRANTOR for the party transferring, selling, or conveying rights.\n"
    "- Use GRANTEE for the party receiving, buying, or acquiring rights.\n"
    "- If the role is unclear, set party_type to null.\n"
    "- For individuals: split the full name into givenname and surname when possible.\n"
    "- designated_status captures roles like TRUSTEE or EXECUTOR that appear alongside the name "
    "(e.g. 'John Smith, Trustee'). Set to null if none is present.\n\n"
    "Example of correctly formatted parties:\n"
    '"individual_parties": [\n'
    '  {"name": "CURTIS M BAREFOOT", "party_type": "GRANTOR", "givenname": "CURTIS M", "surname": "BAREFOOT", "designated_status": null}\n'
    "]\n"
    '"firm_parties": [\n'
    '  {"name": "FIRST FEDERAL BANK", "party_type": "GRANTEE", "designated_status": null}\n'
    "]"
)


def update_prompt(apps, schema_editor):
    Agent = apps.get_model("courtney_async", "Agent")
    Agent.objects.filter(name="extractor").update(system_prompt=EXTRACTOR_PROMPT)


def revert_prompt(apps, schema_editor):
    Agent = apps.get_model("courtney_async", "Agent")
    Agent.objects.filter(name="extractor").update(
        system_prompt=(
            "You are a structured data extraction engine for land record documents. "
            "Extract all relevant fields and return ONLY a valid JSON object. "
            "Do not include any explanation or markdown. Return raw JSON only.\n\n"
            "IMPORTANT RULES FOR PARTIES:\n"
            "- The only valid roles are GRANTOR and GRANTEE. Never use any other term "
            "(not BUYER, SELLER, TRUSTEE, LENDER, PURCHASER, or anything else).\n"
            "- Use GRANTOR for the party transferring, selling, or conveying rights.\n"
            "- Use GRANTEE for the party receiving, buying, or acquiring rights.\n"
            "- If the role is unclear, omit the field (set it to null).\n\n"
            "Example of a correctly formatted party:\n"
            '{"name": "Smith", "givenname": "John A.", "role": "GRANTOR", "type": "I"}'
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ("courtney_async", "0003_update_extractor_prompt"),
    ]

    operations = [
        migrations.RunPython(update_prompt, reverse_code=revert_prompt),
    ]
