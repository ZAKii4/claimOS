import re
import glob

migration_files = glob.glob("migrations/versions/*_initial_enterprise_schema.py")
if not migration_files:
    print("Migration file not found")
    exit(1)

migration_path = migration_files[0]

with open(migration_path, "r") as f:
    content = f.read()

# Foreign keys to extract and add at the end
fks_to_add = """
    op.create_foreign_key('fk_claim_file_policy_id', 'claim_file', 'insurance_policy', ['policy_id'], ['id'])
    op.create_foreign_key('fk_claim_file_claim_type_id', 'claim_file', 'claim_type', ['claim_type_id'], ['id'])
    op.create_foreign_key('fk_claim_file_status_id', 'claim_file', 'claim_status', ['status_id'], ['id'])
    
    op.create_foreign_key('fk_claim_party_claim_id', 'claim_party', 'claim_file', ['claim_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_claim_party_role_id', 'claim_party', 'party_role', ['role_id'], ['id'])
    
    op.create_foreign_key('fk_insurance_policy_insurer_id', 'insurance_policy', 'insurer', ['insurer_id'], ['id'])
    op.create_foreign_key('fk_insurance_policy_policyholder_party_id', 'insurance_policy', 'claim_party', ['policyholder_party_id'], ['id'])
    op.create_foreign_key('fk_insurance_policy_product_type_id', 'insurance_policy', 'product_type', ['product_type_id'], ['id'])
"""

# Remove them from create_table calls (ensure we remove the trailing comma as well)
content = re.sub(r"\s*sa\.ForeignKeyConstraint\(\['claim_type_id'\], \['claim_type\.id'\], \),", "", content)
content = re.sub(r"\s*sa\.ForeignKeyConstraint\(\['policy_id'\], \['insurance_policy\.id'\], \),", "", content)
content = re.sub(r"\s*sa\.ForeignKeyConstraint\(\['status_id'\], \['claim_status\.id'\], \),", "", content)

content = re.sub(r"\s*sa\.ForeignKeyConstraint\(\['claim_id'\], \['claim_file\.id'\], ondelete='CASCADE'\),", "", content)
content = re.sub(r"\s*sa\.ForeignKeyConstraint\(\['role_id'\], \['party_role\.id'\], \),", "", content)

content = re.sub(r"\s*sa\.ForeignKeyConstraint\(\['insurer_id'\], \['insurer\.id'\], \),", "", content)
content = re.sub(r"\s*sa\.ForeignKeyConstraint\(\['policyholder_party_id'\], \['claim_party\.id'\], \),", "", content)
content = re.sub(r"\s*sa\.ForeignKeyConstraint\(\['product_type_id'\], \['product_type\.id'\], \),", "", content)

# Insert the fks at the end of upgrade()
content = re.sub(r"(    # ### end Alembic commands ###)", fks_to_add + r"\n\1", content, count=1)

with open(migration_path, "w") as f:
    f.write(content)

print("Migration fixed!")
