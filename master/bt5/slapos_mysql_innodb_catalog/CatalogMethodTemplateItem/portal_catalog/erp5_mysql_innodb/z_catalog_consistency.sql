DELETE FROM
  consistency
WHERE
<dtml-in uid>
  uid=<dtml-sqlvar sequence-item type="int"><dtml-if sequence-end><dtml-else> OR </dtml-if>
</dtml-in>
;

<dtml-var "'\0'">


INSERT INTO
  consistency
VALUES
<dtml-in prefix="loop" expr="_.range(_.len(uid))">
(
  <dtml-sqlvar expr="uid[loop_item]" type="int">,
  <dtml-sqlvar expr="int(len(checkConsistency[loop_item]) > 0)" type="int">
)
<dtml-if sequence-end><dtml-else>,</dtml-if>
</dtml-in>
