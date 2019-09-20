# inspired by Pack_generateCode128BarcodeImage in sanef-evl project
code_url = code_url + "&trade_no=" + trade_no
return context.Base_generateBarcodeImage('qrcode', code_url)
