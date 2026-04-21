from django.db import migrations

EXTRACTOR_PROMPT = (
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


def update_prompt(apps, schema_editor):
    Agent = apps.get_model("courtney_async", "Agent")
    Agent.objects.filter(name="extractor").update(system_prompt=EXTRACTOR_PROMPT)


def revert_prompt(apps, schema_editor):
    Agent = apps.get_model("courtney_async", "Agent")
    Agent.objects.filter(name="extractor").update(
        system_prompt=(
            "You are a structured data extraction engine for land record documents. "
            "Extract all relevant fields and return ONLY a valid JSON object. "
            "Do not include any explanation or markdown. Return raw JSON only."
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ("courtney_async", "0002_seed_agents"),
    ]

    operations = [
        migrations.RunPython(update_prompt, reverse_code=revert_prompt),
    ]
