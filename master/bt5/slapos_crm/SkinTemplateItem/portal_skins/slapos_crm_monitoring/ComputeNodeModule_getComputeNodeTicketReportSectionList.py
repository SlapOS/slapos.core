from Products.ERP5Form.Report import ReportSection
result=[]

result.append(ReportSection(
              path=context.getPhysicalPath(),
              level=3,
              title=context.Base_translateString('Current Compute Node State'),
              form_id='ComputeNodeModule_viewTicketActivity'))

return result
