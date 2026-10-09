<dtml-let column="
  {'computer': 'computer_security_uid',
   'function': 'function_security_uid',
   'project': 'project_security_uid',
   'user': 'user_security_uid',
   'subscription': 'subscription_security_uid',
   'group': 'group_security_uid',
   'shadow': 'shadow_security_uid',
   '': 'security_uid'}[column_type]
">
SELECT DISTINCT <dtml-var column> AS used_security_uid
FROM catalog
WHERE <dtml-var column> IS NOT NULL
</dtml-let>