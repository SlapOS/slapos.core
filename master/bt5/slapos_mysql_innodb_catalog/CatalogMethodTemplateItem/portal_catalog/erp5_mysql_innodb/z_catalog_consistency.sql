REPLACE INTO
  consistency
  (`uid`, `consistency_error`)
VALUES
<dtml-in prefix="loop" expr="_.range(_.len(uid))">
(
  <dtml-sqlvar expr="uid[loop_item]" type="int">,
  <dtml-sqlvar expr="int((checkConsistency[loop_item] is None) or len(checkConsistency[loop_item]) > 0)" type="int">
)
<dtml-if sequence-end>
<dtml-else>
,
</dtml-if>
</dtml-in>
