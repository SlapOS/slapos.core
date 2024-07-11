import json

contextual_help_list = []
web_site = context.getWebSiteValue()

if web_site is None: 
  return json.dumps(contextual_help_list)

web_site_id = web_site.getRelativeUrl().split('/')[1]
if web_site_id not in ["rapidspacejs", "hostingjs"]:
  return json.dumps(contextual_help_list)

if context.getPortalType() == "Instance Tree":
  if web_site_id == "hostingjs" and context.getSourceReference() == "kvm-cluster":
    contextual_help_list.extend([
      {"title": "Connect noVNC Over IPv4",
      "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Connect.To.A.VPS.Via.VNC.Over.IPv4.On.Rapid.Space"},
      {"title": "Connect noVNC Over IPv6",
      "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Connect.To.A.VPS.Via.VNC.Over.IPv6.On.Rapid.Space"},
      {"title": "Install Default Debian OS",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.VPS.Install.Default.Linux"},
      {"title": "Install Other Linux OS",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Deploy.A.VPS.With.A.Different.Linux.Distribution.On.Rapid.Space"},
      {"title": "Redirect VPS Ports",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Redirect.VPS.Ports.On.Rapid.Space"},
      {"title": "Install IPv6 Inside VPS",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Install.IPv6.Inside.VM"},
      {"title": "SSH to VPS",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Access.A.VPS.Via.Ssh.On.Rapid.Space"},
      {"title": "SSH to VPS",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Access.A.VPS.Via.Ssh.On.Rapid.Space"},
      {"title": "Install Other OS",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Deploy.A.VPS.With.Other.OS.On.Rapid.Space"},
      {"title": "Install Windows OS",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Deploy.A.VPS.With.Windows.On.Rapid.Space"},
      {"title": "Configure IPv6 For Windows",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Configure.IPv6.Address.To.Get.Remote.Access.To.Windows.VPS"},
      {"title": "Monitor VPS",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Monitor.A.VPS.On.Rapid.Space"}
    ])
elif context.getPortalType() == "Accounting Transaction Module":
  if web_site_id == "hostingjs":
    contextual_help_list.extend([
      {"title": "Payment Options",
       "href": "https://handbook.rapid.space/user/faq/rapidspace-Faq.What.Are.The.Payment.Options"}
    ])
elif context.getPortalType() == "Instance Tree Module":
  if web_site_id == "hostingjs":
    contextual_help_list.extend([
      {"title": "Access Services",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Access.Rapid.Space.Services"},
      {"title": "Use Panel",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Use.Rapid.Space.Panel"},
      {"title": "Order A Second Machine",
       "href": "https://handbook.rapid.space/user/faq/rapidspace-Faq.Can.I.Order.A.Second.Machine"},
      {"title": "Get Free Services",
       "href": "https://handbook.rapid.space/user/faq/rapidspace-Faq.Is.There.Any.Free.Services.I.Can.Access"},
      {"title": "Purchase Other Services",
       "href": "https://handbook.rapid.space/user/faq/rapidspace-Faq.Can.I.Purchase.Other.Types.Of.Service"},
      {"title": "Know More Services",
       "href": "https://handbook.rapid.space/user/faq/rapidspace-What.Are.The.Services.That.Rapid.Space.Cloud.Can.Provide"}
    ])
elif context.getPortalType() == "Person Module":
  if web_site_id == "hostingjs":
    contextual_help_list.extend([
      {"title": "Request A Test Account",
       "href": "https://handbook.rapid.space/user/faq/rapidspace-Can.I.Request.A.Test.Account.To.Try"},
      {"title": "Associate With More VMs",
       "href": "http://handbook.rapid.space/user/faq/rapidspace-Faq.My.Account.Is.Associate.With.Only.One.VM"}
    ])
elif context.getPortalType() == "Support Request Module":
  if web_site_id == "hostingjs":
    contextual_help_list.extend([
      {"title": "Add Tickets",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Add.A.Ticket.To.Contact.Rapid.Space.Team"},
      {"title": "Use Panel",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Use.Rapid.Space.Panel"},
      {"title": "User Handbook",
       "href": "https://handbook.rapid.space/user"},
      {"title": "Learning Track",
       "href": "https://handbook.rapid.space/user/rapidspace-Learning.Track"},
      {"title": "User FAQ",
       "href": "https://handbook.rapid.space/user/faq"},
      {"title": "Contacts",
       "href": "https://handbook.rapid.space/contact"}
    ])
elif context.getPortalType() == "Software Release Module":
  if web_site_id == "hostingjs":
    contextual_help_list.extend([
      {"title": "Get Free Services",
       "href": "https://handbook.rapid.space/user/faq/rapidspace-Faq.Is.There.Any.Free.Services.I.Can.Access"}
    ])
elif context.getPortalType() == "Project Module":
  if web_site_id == "hostingjs":
    contextual_help_list.extend([
      {"title": "Add Projects",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Add.A.New.Project"}
    ])
elif context.getPortalType() == "Compute Node Module":
  if web_site_id == "hostingjs":
    contextual_help_list.extend([
      {"title": "Install SlapOS Node On PC",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Install.Slapos.Node.Comp.123"},
      {"title": "Install SlapOS Node On KVM",
       "href": "https://handbook.rapid.space/user/rapidspace-Install.SlapOS.Node.Comp.123.On.Rapid.Space.KVM"},
      {"title": "Associate Compute Nodes",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Associate.A.Computer"}
    ])
elif context.getPortalType() == "Computer Network Module":
  if web_site_id == "hostingjs":
    contextual_help_list.extend([
      {"title": "Add Networks",
       "href": "https://handbook.rapid.space/user/rapidspace-HowTo.Add.A.New.Network"}
    ])
elif context.getPortalType() == "Organisation Module":
  if web_site_id == "hostingjs":
    contextual_help_list.extend([
      {"title": "Classify Nodes",
       "href": "https://handbook.rapid.space/user/slapos-HowTo.Classify.Node.In.A.Network"}
    ])

# Translate titles
for contextual_help in contextual_help_list:
  # Preserve untranslated title for reference.
  contextual_help['data-i18n'] = contextual_help['title']
  contextual_help['title'] = context.Base_translateString(contextual_help['title'])

return json.dumps(contextual_help_list)
