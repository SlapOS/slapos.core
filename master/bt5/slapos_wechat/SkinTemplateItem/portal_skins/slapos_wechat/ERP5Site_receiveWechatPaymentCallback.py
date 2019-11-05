# This script should be called by Wechat payment system to notify us of a payment done.
# Unfortunately, the Wechat payment is doing a POST request with Content type: text/xml"
# so Zope Publisher think it is XMLRPC and doesn't call this script.

# The solution would be to backport this MR https://github.com/zopefoundation/Zope/pull/622
# into our zope and then create the IXmlrpcChecker utility returning always False



#request = container.REQUEST

raise NotImplementedError("This script is not callable by Wechat for now. So we didn't bother implement it.")
