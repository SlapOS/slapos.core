DELETE FROM
  email
WHERE
<dtml-in uid>
  uid=<dtml-sqlvar sequence-item type="int"><dtml-if sequence-end><dtml-else> OR </dtml-if>
</dtml-in>
;

<dtml-var "'\0'"><dtml-let email_list="[]">
  <dtml-in prefix="loop" expr="_.range(_.len(uid))">
    <dtml-if expr="getPortalType[loop_item] in ['Email',]">
      <dtml-call expr="email_list.append(loop_item)">
    </dtml-if>
    <dtml-if expr="getPortalType[loop_item] in ['Software Release', 'Software Product Release Variation', 'Software Installation', 'Software Instance', 'Instance Tree', 'Slave Instance']">
      <dtml-if expr="getValidationState[loop_item] in ('validated', 'published')">
        <dtml-call expr="email_list.append(loop_item)">
      </dtml-if>
    </dtml-if>
  </dtml-in>
  <dtml-if expr="_.len(email_list) > 0">
    INSERT INTO
      email
    VALUES
      <dtml-in prefix="loop" expr="email_list">
      (
        <dtml-sqlvar expr="uid[loop_item]" type="int">,
        <dtml-sqlvar expr="getUrlString[loop_item]" type="string" optional>
      )
      <dtml-if sequence-end><dtml-else>,</dtml-if>
    </dtml-in>
  </dtml-if>
</dtml-let>
