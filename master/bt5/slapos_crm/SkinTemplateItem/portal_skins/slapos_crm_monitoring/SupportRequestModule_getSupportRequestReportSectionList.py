from Products.ERP5Form.Report import ReportSection
result=[]


result.append(ReportSection(
              path=context.getPhysicalPath(),
              level=1,
              title=context.Base_translateString('Service Grade'),
              form_id="SupportRequestModule_viewTicketCurrentStatus"))

return result
